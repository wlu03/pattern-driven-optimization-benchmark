"""
finetune_lora.py
----------------
Fine-tunes Qwen2.5-Coder-7B-Instruct with QLoRA using Unsloth.

Requirements:
    pip install unsloth datasets trl

Run:
    python3 finetune_lora.py
    python3 finetune_lora.py --train train.jsonl --val val.jsonl --output lora_adapter/
"""

# unsloth must be imported before trl/transformers/peft
import unsloth  # noqa: F401
import argparse
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template

BASE_MODEL   = "Qwen/Qwen2.5-Coder-7B-Instruct"
MAX_SEQ_LEN  = 2048   # increase to 4096 if you have VRAM to spare
LORA_RANK    = 16     # 8 = lighter, 32 = more capacity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train",  default="train.jsonl")
    parser.add_argument("--val",    default=None)          # None = no eval
    parser.add_argument("--output", default="lora_adapter/")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch",  type=int, default=2)
    parser.add_argument("--grad_accum", type=int, default=8)
    parser.add_argument("--lr",     type=float, default=2e-4)
    args = parser.parse_args()

    # ── Load model + tokenizer ──────────────────────────────────────────────
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = BASE_MODEL,
        max_seq_length = MAX_SEQ_LEN,
        dtype          = None,   # auto (bfloat16 on Ampere+, float16 otherwise)
        load_in_4bit   = True,   # QLoRA: 4-bit base weights
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r              = LORA_RANK,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj"],
        lora_alpha     = LORA_RANK * 2,
        lora_dropout   = 0,
        bias           = "none",
        use_gradient_checkpointing = "unsloth",
        random_state   = 42,
    )

    tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")

    # ── Load dataset ────────────────────────────────────────────────────────
    data_files = {"train": args.train}
    if args.val:
        data_files["validation"] = args.val
    dataset = load_dataset("json", data_files=data_files)

    def apply_template(batch):
        texts = [
            tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
            for msgs in batch["messages"]
        ]
        return {"text": texts}

    dataset = dataset.map(apply_template, batched=True,
                          remove_columns=dataset["train"].column_names)

    # ── Train ───────────────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model              = model,
        processing_class   = tokenizer,
        train_dataset      = dataset["train"],
        eval_dataset       = dataset["validation"] if "validation" in dataset else None,
        args = SFTConfig(
            dataset_text_field          = "text",
            packing                     = True,
            max_seq_length              = MAX_SEQ_LEN,
            per_device_train_batch_size = args.batch,
            gradient_accumulation_steps = args.grad_accum,
            num_train_epochs            = args.epochs,
            learning_rate               = args.lr,
            warmup_ratio                = 0.05,
            lr_scheduler_type           = "cosine",
            fp16                        = False,
            bf16                        = True,
            logging_steps               = 10,
            eval_strategy               = "epoch" if "validation" in dataset else "no",
            save_strategy               = "epoch",
            save_total_limit            = 2,
            output_dir                  = args.output,
            report_to                   = "none",
        ),
    )

    trainer.train()

    # ── Save LoRA adapter ───────────────────────────────────────────────────
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"\nLoRA adapter saved to {args.output}")
    print("\nNext steps:")
    print("  Option A — serve with vLLM (no merge needed):")
    print("    vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \\")
    print("      --enable-lora \\")
    print(f"      --lora-modules finetuned={args.output}")
    print("\n  Option B — merge weights and export to GGUF for Ollama:")
    print("    python3 merge_and_export.py")


if __name__ == "__main__":
    main()
