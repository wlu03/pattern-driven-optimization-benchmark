"""
merge_and_export.py
-------------------
Merges LoRA adapter into the base model, exports to GGUF, and registers with Ollama.

Requirements:
    pip install unsloth
    brew install llama.cpp   # or build from source for convert-hf-to-gguf.py

Run after finetune_lora.py:
    python3 merge_and_export.py
"""

import subprocess
from unsloth import FastLanguageModel

BASE_MODEL   = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_ADAPTER = "lora_adapter/"
MERGED_DIR   = "merged_model/"
GGUF_PATH    = "qwen2.5-coder-finetuned.Q4_K_M.gguf"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = BASE_MODEL,
    max_seq_length = 2048,
    load_in_4bit   = True,
)

model.load_adapter(LORA_ADAPTER)

# Merge LoRA into base weights (in float16 for conversion)
model = model.merge_and_unload()
model.save_pretrained_merged(MERGED_DIR, tokenizer, save_method="merged_16bit")

# Convert to GGUF (Q4_K_M is a good quality/size tradeoff)
subprocess.run([
    "python3", "llama.cpp/convert_hf_to_gguf.py",
    MERGED_DIR, "--outfile", GGUF_PATH, "--outtype", "q4_k_m"
], check=True)

print(f"GGUF saved: {GGUF_PATH}")
print("\nRegister with Ollama:")
print(f"  echo 'FROM ./{GGUF_PATH}' > Modelfile")
print("  ollama create qwen2.5-coder-finetuned -f Modelfile")
print("\nThen add to models.yaml and run evaluation:")
print("  python3 ../evaluate_llm.py --model qwen2.5-coder-finetuned --strategy generic")
