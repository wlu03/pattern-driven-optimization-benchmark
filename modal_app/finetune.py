"""modal_app/finetune.py — QLoRA fine-tune on Modal using Unsloth.

Reproduces the local LoRA training in fine_tune/finetune_lora.py but on
Modal's L40S GPU (Modal's official Unsloth recommendation for this tier).
The held-out exclusion is enforced by `--exclude held_out` on
prepare_finetune_data.py before calling this; this script trusts the
train/val JSONL it receives.

Usage:

    modal run modal_app/finetune.py::train \
        --base-model Qwen/Qwen2.5-Coder-7B-Instruct \
        --train-jsonl fine_tune/train.jsonl \
        --val-jsonl   fine_tune/val.jsonl \
        --output-name qwen25-coder-7b-taxonomy

Outputs land in the `pdob-adapters` Volume at
/checkpoints/<output-name>/. Pull with `modal volume get pdob-adapters
<output-name>/ ./local_adapters/` once done.
"""
from pathlib import Path

import modal

APP_NAME = "pdob-finetune"

app = modal.App(APP_NAME)

# Image follows Modal's official Unsloth recipe exactly (modal.com/docs/
# examples/unsloth_finetune); unsloth must be imported FIRST in the
# function body.
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
        "wandb==0.21.0",
    )
    .env({"HF_HOME": "/model_cache",
          "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

model_cache_vol   = modal.Volume.from_name("pdob-hf-cache",     create_if_missing=True)
dataset_cache_vol = modal.Volume.from_name("pdob-dataset",      create_if_missing=True)
ckpt_vol          = modal.Volume.from_name("pdob-adapters",     create_if_missing=True)


@app.function(
    image=train_image,
    gpu="L40S",                       # Modal's recommended Unsloth GPU
    timeout=6 * 60 * 60,              # 6 h cap
    retries=2,
    volumes={
        "/model_cache":   model_cache_vol,
        "/dataset_cache": dataset_cache_vol,
        "/checkpoints":   ckpt_vol,
    },
)
def train(
    base_model: str,
    train_jsonl_bytes: bytes,
    val_jsonl_bytes:   bytes,
    output_name: str,
    max_seq_length: int = 4096,
    lora_r: int = 16,
    lora_alpha: int = 32,
    learning_rate: float = 2e-4,
    num_train_epochs: int = 3,
    per_device_batch_size: int = 2,
    grad_accum_steps: int = 8,
):
    """Train a QLoRA adapter on the supplied train/val JSONL.

    Returns the relative path under /checkpoints/ where the adapter
    landed (committed to the pdob-adapters Volume).
    """
    import unsloth  # MUST be first import
    from unsloth import FastLanguageModel
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig
    import json

    # Write JSONL to local container disk
    train_path = Path("/dataset_cache") / f"{output_name}_train.jsonl"
    val_path   = Path("/dataset_cache") / f"{output_name}_val.jsonl"
    train_path.write_bytes(train_jsonl_bytes)
    val_path.write_bytes(val_jsonl_bytes)

    # Load base + apply LoRA
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        target_modules=["q_proj","k_proj","v_proj","o_proj",
                        "gate_proj","up_proj","down_proj"],
        lora_alpha=lora_alpha,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    def _read_jsonl(p: Path):
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    train_ds = Dataset.from_list(_read_jsonl(train_path))
    val_ds   = Dataset.from_list(_read_jsonl(val_path))

    out_dir = Path("/checkpoints") / output_name
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = SFTConfig(
        output_dir=str(out_dir),
        per_device_train_batch_size=per_device_batch_size,
        gradient_accumulation_steps=grad_accum_steps,
        warmup_steps=10,
        num_train_epochs=num_train_epochs,
        learning_rate=learning_rate,
        logging_steps=10,
        save_steps=200,
        save_total_limit=2,
        bf16=True,
        report_to="none",
        max_length=max_seq_length,
    )
    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer,
        train_dataset=train_ds, eval_dataset=val_ds,
        args=cfg,
        dataset_text_field="text",
    )
    trainer.train()

    # Save merged adapter
    model.save_pretrained(str(out_dir / "adapter"))
    tokenizer.save_pretrained(str(out_dir / "adapter"))
    ckpt_vol.commit()
    return f"{output_name}/adapter"


@app.local_entrypoint()
def main(
    base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
    train_jsonl: str = "fine_tune/train.jsonl",
    val_jsonl:   str = "fine_tune/val.jsonl",
    output_name: str = "qwen25-coder-7b-taxonomy",
):
    train_bytes = Path(train_jsonl).read_bytes()
    val_bytes   = Path(val_jsonl).read_bytes()
    print(f"Submitting fine-tune of {base_model} -> {output_name}")
    print(f"  train: {train_jsonl} ({len(train_bytes)} bytes)")
    print(f"  val:   {val_jsonl}   ({len(val_bytes)} bytes)")
    rel = train.remote(
        base_model=base_model,
        train_jsonl_bytes=train_bytes,
        val_jsonl_bytes=val_bytes,
        output_name=output_name,
    )
    print(f"Adapter saved to volume pdob-adapters at: {rel}")
    print(f"Pull locally with:")
    print(f"  modal volume get pdob-adapters {rel} ./fine_tune/lora_fine_tuning/{output_name}/")
