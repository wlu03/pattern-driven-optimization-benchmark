"""modal_app/finetune_weak3.py — QLoRA fine-tune the 3 weakest ~7B models on
Modal, merge to 16-bit, and stage eval-ready weights on a Modal volume.

Targets (the 3 weakest ~7B-tier models by sweep pass@1; see
results/category_difficulty.txt for the wider ranking):

    deepseek-r1-distill-qwen-7b   26.7%   (reasoning; SFT teaches direct output)
    yi-coder-9b                   66.2%
    opencoder-8b                  76.7%

(Qwen2.5-Coder-7B at 81.4% is the strongest of the tier and is intentionally
left as the un-tuned ceiling reference.)

Training data is fine_tune/{train,val}.jsonl — chat format produced by
fine_tune/prepare_finetune_data.py, which EXCLUDES dataset/held_out/ so the
held-out set stays a clean contamination-defense eval (this is exactly what the
#4 fine-tune-vs-baseline paired-Wilcoxon test needs). Each example is
{"messages": [user(optimize-prompt), assistant(fast.c renamed `optimized`)]}.

Outputs: merged 16-bit weights at /finetuned/<name>/ on the `pdob-finetuned`
volume. modal_app/inference.py mounts that volume and registers a `<name>` model
key per fine-tune, so eval is the unchanged pipeline:

    modal run modal_app/finetune_weak3.py                 # train all 3 (parallel)
    modal run modal_app/finetune_weak3.py --only opencoder-8b-ft
    modal run modal_app/inference.py --model opencoder-8b-ft --strategy taxonomy-guided
    # then score + compare exactly like the base sweep.

Pull weights locally instead:
    modal volume get pdob-finetuned opencoder-8b-ft/ ./fine_tune/merged/opencoder-8b-ft/
"""
from pathlib import Path

import modal

APP_NAME = "pdob-finetune-weak3"
app = modal.App(APP_NAME)

# The 3 weakest ~7B-tier targets. `name` is the eval model-key that
# inference.py exposes (it appends nothing — keep these in sync with the
# _FINETUNED map in inference.py). `reasoning` only affects the doc note;
# SFT on no-CoT targets is what teaches a reasoning model to answer directly.
TARGETS = [
    {"base": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "name": "r1-distill-qwen-7b-ft", "reasoning": True},
    {"base": "01-ai/Yi-Coder-9B-Chat",                  "name": "yi-coder-9b-ft",        "reasoning": False},
    {"base": "infly/OpenCoder-8B-Instruct",             "name": "opencoder-8b-ft",       "reasoning": False},
]

# Image follows Modal's official Unsloth recipe (unsloth must be imported FIRST
# inside the function). Mirrors modal_app/finetune.py.
train_image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "accelerate==1.9.0",
        "datasets==3.6.0",
        "peft==0.16.0",
        "transformers==4.54.0",
        "trl==0.19.1",
        "unsloth[cu128-torch270]==2025.7.8",
        "unsloth_zoo==2025.7.10",
        "hf-transfer==0.1.9",
    )
    .env({"HF_HOME": "/model_cache", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache_vol = modal.Volume.from_name("pdob-hf-cache",   create_if_missing=True)
ft_vol       = modal.Volume.from_name("pdob-finetuned",  create_if_missing=True)


def _maybe_hf_secret():
    """Yi-Coder / some bases may be gated; attach the HF secret if present."""
    try:
        return [modal.Secret.from_name("huggingface")]
    except Exception:
        return []


@app.function(
    image=train_image,
    gpu="L40S",                      # 48 GB — comfortable for 7-9B QLoRA + merge
    timeout=6 * 60 * 60,
    retries=1,
    secrets=_maybe_hf_secret(),
    volumes={"/model_cache": hf_cache_vol, "/finetuned": ft_vol},
)
def finetune_and_merge(
    base_model: str,
    name: str,
    train_jsonl_bytes: bytes,
    val_jsonl_bytes: bytes,
    max_seq_length: int = 4096,
    lora_r: int = 16,
    lora_alpha: int = 32,
    learning_rate: float = 2e-4,
    num_train_epochs: int = 3,
    per_device_batch_size: int = 2,
    grad_accum_steps: int = 8,
) -> str:
    """Train a QLoRA adapter on the supplied chat-format JSONL, merge it into
    16-bit base weights, and write the merged model to /finetuned/<name>/.
    Returns the volume path. vLLM loads the merged dir directly for eval."""
    import json

    import unsloth  # MUST be imported before transformers/trl
    from unsloth import FastLanguageModel
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=lora_alpha,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # The JSONL is conversational ({"messages": [...]}). Render each example to
    # a single string with THIS model's chat template, so training matches how
    # inference.py formats prompts at eval time (apply_chat_template).
    def _render(raw: bytes) -> list[dict]:
        rows = []
        for line in raw.decode().splitlines():
            line = line.strip()
            if not line:
                continue
            msgs = json.loads(line)["messages"]
            rows.append({"text": tokenizer.apply_chat_template(msgs, tokenize=False)})
        return rows

    train_ds = Dataset.from_list(_render(train_jsonl_bytes))
    val_ds = Dataset.from_list(_render(val_jsonl_bytes))
    print(f"[{name}] train={len(train_ds)} val={len(val_ds)} examples")

    out_dir = Path("/finetuned") / name
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = SFTConfig(
        output_dir=str(out_dir / "_ckpt"),
        per_device_train_batch_size=per_device_batch_size,
        gradient_accumulation_steps=grad_accum_steps,
        warmup_steps=10,
        num_train_epochs=num_train_epochs,
        learning_rate=learning_rate,
        logging_steps=10,
        save_steps=200,
        save_total_limit=1,
        bf16=True,
        report_to="none",
        max_length=max_seq_length,
        dataset_text_field="text",
    )
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        args=cfg,
    )
    trainer.train()

    # Merge LoRA into the base and save full 16-bit weights (+ tokenizer) so
    # vLLM can serve the dir with no adapter plumbing.
    model.save_pretrained_merged(str(out_dir), tokenizer, save_method="merged_16bit")
    ft_vol.commit()
    print(f"[{name}] merged 16-bit weights -> /finetuned/{name}")
    return f"/finetuned/{name}"


@app.local_entrypoint()
def main(
    only: str = "",
    epochs: int = 3,
    train_jsonl: str = "fine_tune/train.jsonl",
    val_jsonl: str = "fine_tune/val.jsonl",
):
    """Submit fine-tunes for the 3 weak targets (or one, via --only <name>)."""
    train_bytes = Path(train_jsonl).read_bytes()
    val_bytes = Path(val_jsonl).read_bytes()
    targets = [t for t in TARGETS if not only or t["name"] == only]
    if not targets:
        raise SystemExit(f"--only {only!r} matched no target; choose from "
                         f"{[t['name'] for t in TARGETS]}")

    print(f"Submitting {len(targets)} QLoRA fine-tune(s) to Modal "
          f"(train={len(train_bytes)}B val={len(val_bytes)}B, epochs={epochs}):")
    for t in targets:
        print(f"  {t['base']} -> {t['name']}")

    # Spawn all in parallel (independent L40S jobs), then collect.
    handles = [
        (t["name"], finetune_and_merge.spawn(
            base_model=t["base"], name=t["name"],
            train_jsonl_bytes=train_bytes, val_jsonl_bytes=val_bytes,
            num_train_epochs=epochs))
        for t in targets
    ]
    print("\nWaiting for completion...")
    for name, h in handles:
        path = h.get()
        print(f"  ✓ {name} -> {path}")

    print("\nEval each with the existing pipeline (writes scoring-ready completions):")
    for t in targets:
        print(f"  modal run modal_app/inference.py --model {t['name']} "
              f"--strategy taxonomy-guided")
    print("\nOr pull the weights locally:")
    for t in targets:
        print(f"  modal volume get pdob-finetuned {t['name']}/ "
              f"./fine_tune/merged/{t['name']}/")
