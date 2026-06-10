"""modal_app/finetune_sweep.py — hyperparameter sweep + recipe upgrades for the
fine-tune-transfer experiment.

Phase-1 baseline (finetune_weak3.py) overfit: narrow QLoRA on a small model
regressed on held-out (catastrophic forgetting). This sweep varies the
overfitting knobs and folds in the recommended recipe changes:

  * epochs / learning-rate / LoRA rank / LoRA dropout  (regularization grid)
  * completion-only loss (mask the prompt; loss only on the assistant answer)
  * replay data (mix a general code-SFT slice so it doesn't collapse onto the
    27 benchmark patterns) — anti-catastrophic-forgetting

Sweep subjects: the model that regressed most (qwen2.5-coder-1.5b) and the most
promising reasoning model (r1-distill-qwen-7b). Each config trains both, merges
to 16-bit, and stages on the pdob-finetuned volume as `<short>-<config>-ft`,
which modal_app/inference.py auto-registers for the held-out eval.

Held-out is still excluded from training (train data predates it; see
fine_tune/prepare_finetune_data.py).

Usage:
    modal run modal_app/finetune_sweep.py                      # full grid
    modal run modal_app/finetune_sweep.py --only qwen2.5-coder-1.5b-gentle-ft
    modal run modal_app/inference.py --model qwen2.5-coder-1.5b-gentle-ft --strategy taxonomy-guided
"""
from pathlib import Path

import modal

APP_NAME = "pdob-finetune-sweep"
app = modal.App(APP_NAME)

# Sweep subjects (short = volume/eval key stem; base_key = inference.py MODELS key
# whose decode config the *-ft variants inherit).
SWEEP_MODELS = [
    {"base": "Qwen/Qwen2.5-Coder-1.5B-Instruct",        "short": "qwen2.5-coder-1.5b",   "base_key": "qwen2.5-coder-1.5b"},
    {"base": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "short": "r1-distill-qwen-7b",   "base_key": "deepseek-r1-distill-qwen-7b"},
]

# Regularization grid. `baseline` reproduces the phase-1 overfit recipe as a
# control; the rest dial down memorization and add completion-only / replay.
CONFIGS = [
    {"name": "baseline",       "epochs": 3, "lr": 2e-4, "r": 16, "alpha": 32, "dropout": 0.0,  "completion_only": False, "replay_frac": 0.0},
    {"name": "gentle",         "epochs": 1, "lr": 1e-4, "r": 16, "alpha": 32, "dropout": 0.1,  "completion_only": True,  "replay_frac": 0.0},
    {"name": "gentle-lowrank", "epochs": 1, "lr": 1e-4, "r": 8,  "alpha": 16, "dropout": 0.1,  "completion_only": True,  "replay_frac": 0.0},
    {"name": "medium",         "epochs": 2, "lr": 1e-4, "r": 16, "alpha": 32, "dropout": 0.05, "completion_only": True,  "replay_frac": 0.0},
    {"name": "lowlr",          "epochs": 2, "lr": 5e-5, "r": 16, "alpha": 32, "dropout": 0.1,  "completion_only": True,  "replay_frac": 0.0},
    {"name": "replay",         "epochs": 2, "lr": 1e-4, "r": 16, "alpha": 32, "dropout": 0.05, "completion_only": True,  "replay_frac": 0.25},
    {"name": "gentle-replay",  "epochs": 1, "lr": 1e-4, "r": 8,  "alpha": 16, "dropout": 0.1,  "completion_only": True,  "replay_frac": 0.25},
]


def sweep_variants() -> dict:
    """{eval_model_key: base_key} for every (model, config) — used by inference.py."""
    return {f"{m['short']}-{c['name']}-ft": m["base_key"]
            for m in SWEEP_MODELS for c in CONFIGS}


train_image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "accelerate==1.9.0", "datasets==3.6.0", "peft==0.16.0",
        "transformers==4.54.0", "trl==0.19.1",
        "unsloth[cu128-torch270]==2025.7.8", "unsloth_zoo==2025.7.10",
        "hf-transfer==0.1.9",
    )
    .env({"HF_HOME": "/model_cache", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache_vol = modal.Volume.from_name("pdob-hf-cache",  create_if_missing=True)
ft_vol       = modal.Volume.from_name("pdob-finetuned", create_if_missing=True)


def _maybe_hf_secret():
    try:
        return [modal.Secret.from_name("huggingface")]
    except Exception:
        return []


@app.function(
    image=train_image, gpu="L40S", timeout=6 * 60 * 60, retries=1,
    secrets=_maybe_hf_secret(),
    volumes={"/model_cache": hf_cache_vol, "/finetuned": ft_vol},
)
def train_one(
    base_model: str, name: str,
    train_jsonl_bytes: bytes, val_jsonl_bytes: bytes,
    epochs: int, lr: float, lora_r: int, lora_alpha: int,
    dropout: float, completion_only: bool, replay_frac: float,
    max_seq_length: int = 4096,
):
    """Train one (model, config) QLoRA, merge to 16-bit -> /finetuned/<name>."""
    import json

    out = Path("/finetuned") / name
    if (out / "config.json").exists():
        print(f"[{name}] already merged on volume — skipping")
        return f"/finetuned/{name}"

    import unsloth  # noqa: F401  (must precede transformers/trl)
    from unsloth import FastLanguageModel
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model, max_seq_length=max_seq_length, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(
        model, r=lora_r, lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=dropout, bias="none",
        use_gradient_checkpointing="unsloth", random_state=42)

    def _msgs(raw: bytes):
        return [json.loads(l)["messages"] for l in raw.decode().splitlines() if l.strip()]
    task_msgs = _msgs(train_jsonl_bytes)

    # Replay: mix a general code-SFT slice to fight catastrophic forgetting.
    replay_msgs = []
    if replay_frac > 0:
        from datasets import load_dataset
        n_rep = int(len(task_msgs) * replay_frac / max(1e-9, 1 - replay_frac))
        try:
            rep = load_dataset("sahil2801/CodeAlpaca-20k", split=f"train[:{n_rep}]")
            for ex in rep:
                instr = ex["instruction"] + (("\n\n" + ex["input"]) if ex.get("input") else "")
                replay_msgs.append([{"role": "user", "content": instr},
                                    {"role": "assistant", "content": ex["output"]}])
            print(f"[{name}] replay: +{len(replay_msgs)} general code-SFT examples")
        except Exception as e:
            print(f"[{name}] replay load failed ({e}); continuing without replay")

    all_msgs = task_msgs + replay_msgs

    # completion_only -> conversational dataset + assistant-only loss (mask the
    # prompt). Falls back to full-sequence text rendering if trl rejects it.
    cfg_kwargs = dict(
        output_dir="/finetuned/_ckpt_" + name,
        per_device_train_batch_size=2, gradient_accumulation_steps=8,
        warmup_steps=10, num_train_epochs=epochs, learning_rate=lr,
        logging_steps=10, save_strategy="no", bf16=True, report_to="none",
        max_length=max_seq_length,
    )
    # Render to text with the model's chat template; for completion-only we
    # then mask the prompt tokens via Unsloth's train_on_responses_only.
    ds = Dataset.from_list(
        [{"text": tokenizer.apply_chat_template(m, tokenize=False)} for m in all_msgs])
    trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=ds,
                         args=SFTConfig(dataset_text_field="text", **cfg_kwargs))
    if completion_only:
        from unsloth.chat_templates import train_on_responses_only
        if "DeepSeek-R1" in base_model or "r1-distill" in name:
            instr_part, resp_part = "<｜User｜>", "<｜Assistant｜>"
        else:  # Qwen ChatML
            instr_part, resp_part = "<|im_start|>user\n", "<|im_start|>assistant\n"
        try:
            trainer = train_on_responses_only(
                trainer, instruction_part=instr_part, response_part=resp_part)
            print(f"[{name}] completion-only via train_on_responses_only ({resp_part!r})")
        except Exception as e:
            print(f"[{name}] train_on_responses_only failed ({e}); full-sequence")

    print(f"[{name}] train n={len(all_msgs)} epochs={epochs} lr={lr} r={lora_r} "
          f"dropout={dropout} completion_only={completion_only} replay={replay_frac}")
    trainer.train()

    out = Path("/finetuned") / name
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_merged(str(out), tokenizer, save_method="merged_16bit")
    ft_vol.commit()
    print(f"[{name}] merged -> /finetuned/{name}")
    return f"/finetuned/{name}"


@app.local_entrypoint()
def main(only: str = "", train_jsonl: str = "fine_tune/train.jsonl",
         val_jsonl: str = "fine_tune/val.jsonl"):
    tb = Path(train_jsonl).read_bytes()
    vb = Path(val_jsonl).read_bytes()
    jobs = []
    for m in SWEEP_MODELS:
        for c in CONFIGS:
            name = f"{m['short']}-{c['name']}-ft"
            if only and name != only:
                continue
            jobs.append((name, train_one.spawn(
                base_model=m["base"], name=name,
                train_jsonl_bytes=tb, val_jsonl_bytes=vb,
                epochs=c["epochs"], lr=c["lr"], lora_r=c["r"], lora_alpha=c["alpha"],
                dropout=c["dropout"], completion_only=c["completion_only"],
                replay_frac=c["replay_frac"])))
    print(f"Submitted {len(jobs)} sweep fine-tunes:")
    for name, _ in jobs:
        print(f"  {name}")
    for name, h in jobs:
        print(f"  ✓ {name} -> {h.get()}")
    print("\nEval e.g.:  modal run modal_app/inference.py "
          "--model qwen2.5-coder-1.5b-gentle-ft --strategy taxonomy-guided")
