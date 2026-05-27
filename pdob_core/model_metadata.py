"""Public-knowledge metadata for the model IDs in ``models.yaml``.

Per-model values cover (family, param_count_b, cost_in_per_1m_tok,
cost_out_per_1m_tok, reasoning). They reflect a public-pricing snapshot
roughly late-2025 / early-2026; pricing and parameter disclosures drift,
so values may be stale by the time a reader runs analysis scripts.

Conservative defaults: anything we are not confident about is left ``None``
instead of guessed. Models with no entry resolve via :func:`get_metadata`
to a stub with ``family=Unknown`` and all numeric fields ``None``.

For MoE models, ``param_count_b`` reports TOTAL parameters (not active per
token) — easier to defend as "size of the artifact" and avoids guessing at
each architecture's routing.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModelMeta:
    family: str                                   # Claude, GPT, DeepSeek, Llama, ...
    param_count_b: Optional[float]                # billions of total parameters
    cost_in_per_1m_tok: Optional[float]           # USD per 1M input tokens
    cost_out_per_1m_tok: Optional[float]          # USD per 1M output tokens
    reasoning: bool                               # has explicit reasoning / chain mode


# ──────────────────────────────────────────────────────────────────────────
# Hand-curated lookup. Keys match the ``id:`` field in models.yaml exactly.
# ──────────────────────────────────────────────────────────────────────────

MODEL_METADATA: dict[str, ModelMeta] = {
    # ── Anthropic Claude ──────────────────────────────────────────────────
    # Param counts not publicly disclosed. Pricing per anthropic.com (Mar 2025).
    "claude-opus-4-6":   ModelMeta("Claude", None, 15.00, 75.00, False),
    "claude-sonnet-4-6": ModelMeta("Claude", None,  3.00, 15.00, False),
    "claude-haiku-4-5":  ModelMeta("Claude", None,  1.00,  5.00, False),

    # ── OpenAI ────────────────────────────────────────────────────────────
    # Param counts undisclosed. Pricing per openai.com pricing page (early 2025).
    "gpt-4o":      ModelMeta("GPT",  None, 2.50, 10.00, False),
    "gpt-4o-mini": ModelMeta("GPT",  None, 0.15,  0.60, False),
    "o3-mini":     ModelMeta("GPT",  None, 1.10,  4.40, True),

    # ── DeepSeek ──────────────────────────────────────────────────────────
    # V3: 671B total / 37B active (MoE). R1: same backbone, RL-tuned.
    # Pricing per api-docs.deepseek.com (off-peak rates omitted; uses standard).
    "deepseek-v3": ModelMeta("DeepSeek", 671.0, 0.27, 1.10, False),
    "deepseek-r1": ModelMeta("DeepSeek", 671.0, 0.55, 2.19, True),

    # ── Google Gemini ─────────────────────────────────────────────────────
    "gemini-2-flash": ModelMeta("Gemini", None, 0.10, 0.40, False),
    "gemini-2-pro":   ModelMeta("Gemini", None, None, None,  False),

    # ── Meta Llama (Together AI hosting) ──────────────────────────────────
    # Pricing per together.ai/pricing for "Turbo" SKUs. Param counts public.
    "llama-3.1-8b-together":   ModelMeta("Llama",   8.0, 0.18, 0.18, False),
    "llama-3.1-70b-together":  ModelMeta("Llama",  70.0, 0.88, 0.88, False),
    "llama-3.1-405b-together": ModelMeta("Llama", 405.0, 3.50, 3.50, False),
    "llama-3.2-11b-together":  ModelMeta("Llama",  11.0, 0.18, 0.18, False),
    "llama-3.3-70b-together":  ModelMeta("Llama",  70.0, 0.88, 0.88, False),

    # ── Mistral / Mixtral ─────────────────────────────────────────────────
    "mistral-7b-together":     ModelMeta("Mistral",   7.0, 0.20, 0.20, False),
    "mixtral-8x7b-together":   ModelMeta("Mistral",  46.7, 0.60, 0.60, False),  # 46.7B total
    "mixtral-8x22b-together":  ModelMeta("Mistral", 141.0, 1.20, 1.20, False),  # 141B total

    # ── Google Gemma 2 ────────────────────────────────────────────────────
    "gemma2-9b-together":  ModelMeta("Gemma",  9.0, 0.30, 0.30, False),
    "gemma2-27b-together": ModelMeta("Gemma", 27.0, 0.80, 0.80, False),

    # ── Microsoft Phi ─────────────────────────────────────────────────────
    "phi-3-mini-together":   ModelMeta("Phi",  3.8, 0.10, 0.10, False),
    "phi-3-medium-together": ModelMeta("Phi", 14.0, 0.30, 0.30, False),

    # ── Alibaba Qwen 2.5 ──────────────────────────────────────────────────
    "qwen2.5-7b-together":  ModelMeta("Qwen",  7.0, 0.30, 0.30, False),
    "qwen2.5-72b-together": ModelMeta("Qwen", 72.0, 1.20, 1.20, False),

    # ── Falcon ────────────────────────────────────────────────────────────
    "falcon-7b-together":  ModelMeta("Falcon",  7.0, 0.20, 0.20, False),
    "falcon-40b-together": ModelMeta("Falcon", 40.0, 0.80, 0.80, False),

    # ── Groq-hosted (same weights as Together, different price) ───────────
    "llama-3.1-8b-groq":   ModelMeta("Llama",   8.0, 0.05, 0.08, False),
    "llama-3.1-70b-groq":  ModelMeta("Llama",  70.0, 0.59, 0.79, False),
    "mixtral-8x7b-groq":   ModelMeta("Mistral", 46.7, 0.24, 0.24, False),
    "gemma2-9b-groq":      ModelMeta("Gemma",   9.0, 0.20, 0.20, False),

    # ── Ollama local (no API cost; param count from model card) ───────────
    "llama3.1-ollama":           ModelMeta("Llama",    8.0, 0.0, 0.0, False),
    "llama3.2-ollama":           ModelMeta("Llama",    3.0, 0.0, 0.0, False),
    "mistral-ollama":            ModelMeta("Mistral",  7.0, 0.0, 0.0, False),
    "mixtral-ollama":            ModelMeta("Mistral", 46.7, 0.0, 0.0, False),
    "gemma2-ollama":             ModelMeta("Gemma",    9.0, 0.0, 0.0, False),
    "phi3-ollama":               ModelMeta("Phi",      3.8, 0.0, 0.0, False),
    "phi4-ollama":               ModelMeta("Phi",     14.0, 0.0, 0.0, False),
    "qwen2.5-ollama":            ModelMeta("Qwen",     7.0, 0.0, 0.0, False),
    "qwen2.5-coder-7b-ollama":   ModelMeta("Qwen",     7.0, 0.0, 0.0, False),
    "falcon-ollama":             ModelMeta("Falcon",   7.0, 0.0, 0.0, False),

    # ── LoRA fine-tunes (base: Qwen2.5-Coder-7B, 4-bit quantized) ─────────
    "qwen-lora-generic":   ModelMeta("Qwen", 7.0, 0.0, 0.0, False),
    "qwen-lora-pattern":   ModelMeta("Qwen", 7.0, 0.0, 0.0, False),
    "qwen-lora-taxonomy":  ModelMeta("Qwen", 7.0, 0.0, 0.0, False),
}


_UNKNOWN = ModelMeta(family="Unknown", param_count_b=None,
                     cost_in_per_1m_tok=None, cost_out_per_1m_tok=None,
                     reasoning=False)


def get_metadata(model_id: str) -> ModelMeta:
    """Return ModelMeta for ``model_id`` or an Unknown stub if not in the table."""
    return MODEL_METADATA.get(model_id, _UNKNOWN)


__all__ = ["ModelMeta", "MODEL_METADATA", "get_metadata"]
