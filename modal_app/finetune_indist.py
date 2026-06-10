"""modal_app/finetune_indist.py — epoch sweep on the CLEAN variant-level split,
to map the in-distribution-transfer vs OOD-forgetting crossover.

Trains on fine_tune/train_indist.jsonl (whole base-pattern variants held out, so
fine_tune/heldout_indist_variants.txt is a genuine in-distribution test). Sweeps
EPOCHS with an otherwise-fixed researched recipe (lr 2e-4 — "the right LR makes
LoRA ≈ full FT", Thinking Machines; alpha=2r; dropout 0.1; completion-only loss).

Expectation (Kumar et al. 2022, feature distortion): as epochs increase,
IN-DISTRIBUTION held-out pass@1 rises (the model specializes on the trained
skills) while the OOD contamination held-out regresses (forgetting). Evaluating
both makes the specialization↔generalization tradeoff explicit.

Variants land as `<short>-indist-ep<N>-ft` on the pdob-finetuned volume;
inference.py registers them for eval.

Usage:
    modal run modal_app/finetune_indist.py
    modal run modal_app/inference.py --model qwen2.5-coder-1.5b-indist-ep6-ft --strategy pattern-aware
"""
from pathlib import Path

import modal

APP_NAME = "pdob-finetune-indist"
app = modal.App(APP_NAME)

MODELS = [
    {"base": "Qwen/Qwen2.5-Coder-1.5B-Instruct",        "short": "qwen2.5-coder-1.5b", "base_key": "qwen2.5-coder-1.5b"},
    {"base": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "short": "r1-distill-qwen-7b", "base_key": "deepseek-r1-distill-qwen-7b"},
]
EPOCHS = [1, 3, 6, 10]            # the sweep axis
LR, LORA_R, LORA_ALPHA, DROPOUT = 2e-4, 16, 32, 0.1   # researched fixed recipe


def indist_variants() -> dict:
    """{eval_model_key: base_key} — used by inference.py."""
    return {f"{m['short']}-indist-ep{e}-ft": m["base_key"] for m in MODELS for e in EPOCHS}


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


@app.function(image=train_image, gpu="L40S", timeout=6 * 60 * 60, retries=1,
              secrets=_maybe_hf_secret(),
              volumes={"/model_cache": hf_cache_vol, "/finetuned": ft_vol})
def train_one(base_model: str, name: str, train_jsonl_bytes: bytes,
              epochs: int, max_seq_length: int = 4096):
    import json
    out = Path("/finetuned") / name
    if (out / "config.json").exists():
        print(f"[{name}] already merged — skipping")
        return f"/finetuned/{name}"

    import unsloth  # noqa: F401
    from unsloth import FastLanguageModel
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tok = FastLanguageModel.from_pretrained(
        model_name=base_model, max_seq_length=max_seq_length, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(
        model, r=LORA_R, lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=DROPOUT, bias="none",
        use_gradient_checkpointing="unsloth", random_state=42)

    msgs = [json.loads(l)["messages"] for l in train_jsonl_bytes.decode().splitlines() if l.strip()]
    ds = Dataset.from_list([{"text": tok.apply_chat_template(m, tokenize=False)} for m in msgs])
    trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=ds, args=SFTConfig(
        output_dir=f"/finetuned/_ckpt_{name}", per_device_train_batch_size=2,
        gradient_accumulation_steps=8, warmup_ratio=0.05, num_train_epochs=epochs,
        learning_rate=LR, logging_steps=20, save_strategy="no", bf16=True,
        report_to="none", max_length=max_seq_length, dataset_text_field="text"))
    # completion-only loss (mask the prompt)
    from unsloth.chat_templates import train_on_responses_only
    if "DeepSeek-R1" in base_model or "r1-distill" in name:
        ip, rp = "<｜User｜>", "<｜Assistant｜>"
    else:
        ip, rp = "<|im_start|>user\n", "<|im_start|>assistant\n"
    try:
        trainer = train_on_responses_only(trainer, instruction_part=ip, response_part=rp)
        print(f"[{name}] completion-only ({rp!r})")
    except Exception as e:
        print(f"[{name}] completion-only failed ({e}); full-sequence")

    print(f"[{name}] train n={len(msgs)} epochs={epochs} lr={LR} r={LORA_R}")
    trainer.train()
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_merged(str(out), tok, save_method="merged_16bit")
    ft_vol.commit()
    print(f"[{name}] merged -> /finetuned/{name}")
    return f"/finetuned/{name}"


@app.local_entrypoint()
def main(only: str = "", train_jsonl: str = "fine_tune/train_indist.jsonl"):
    tb = Path(train_jsonl).read_bytes()
    jobs = []
    for m in MODELS:
        for e in EPOCHS:
            name = f"{m['short']}-indist-ep{e}-ft"
            if only and name != only:
                continue
            jobs.append((name, train_one.spawn(
                base_model=m["base"], name=name, train_jsonl_bytes=tb, epochs=e)))
    print(f"Submitted {len(jobs)} epoch-sweep fine-tunes (clean split):")
    for name, _ in jobs:
        print(f"  {name}")
    for name, h in jobs:
        print(f"  ✓ {name} -> {h.get()}")
