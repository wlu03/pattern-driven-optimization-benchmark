import os
import sys
import time
from typing import Callable


def load_model_config(config_path: str = "models.yaml") -> dict:
    """Load models.yaml and return {model_id: model_cfg} plus defaults."""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    defaults = cfg.get("defaults", {})
    models = {}
    for m in cfg.get("models", []):
        merged = {**defaults, **m}
        models[m["id"]] = merged
    return models


def _call_anthropic(prompt: str, model_cfg: dict) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed: pip install anthropic")

    api_key = os.environ.get(model_cfg["api_key_env"])
    if not api_key:
        raise RuntimeError(f"Environment variable {model_cfg['api_key_env']} is not set")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model_cfg["model_name"],
        max_tokens=model_cfg.get("max_tokens", 2048),
        temperature=model_cfg.get("temperature", 0.2),
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai(prompt: str, model_cfg: dict) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")

    api_key = os.environ.get(model_cfg.get("api_key_env", ""))
    if not api_key:
        raise RuntimeError(f"Environment variable {model_cfg.get('api_key_env')} is not set")

    kwargs = {"api_key": api_key}
    if model_cfg.get("base_url"):
        kwargs["base_url"] = model_cfg["base_url"]

    client = OpenAI(**kwargs)

    create_kwargs = dict(
        model=model_cfg["model_name"],
        messages=[{"role": "user", "content": prompt}],
    )
    if not model_cfg["model_name"].startswith("o"):
        create_kwargs["temperature"] = model_cfg.get("temperature", 0.2)
        create_kwargs["max_tokens"] = model_cfg.get("max_tokens", 2048)
    else:
        create_kwargs["max_completion_tokens"] = model_cfg.get("max_tokens", 4096)

    response = client.chat.completions.create(**create_kwargs)
    return response.choices[0].message.content


def _call_ollama(prompt: str, model_cfg: dict) -> str:
    """Ollama local server — OpenAI-compatible, no auth required."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")

    base_url = model_cfg.get("base_url", "http://localhost:11434/v1")
    client = OpenAI(api_key="ollama", base_url=base_url)
    response = client.chat.completions.create(
        model=model_cfg["model_name"],
        messages=[{"role": "user", "content": prompt}],
        temperature=model_cfg.get("temperature", 0.2),
        max_tokens=model_cfg.get("max_tokens", 2048),
    )
    return response.choices[0].message.content


def _call_google(prompt: str, model_cfg: dict) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai not installed: pip install google-generativeai")

    api_key = os.environ.get(model_cfg["api_key_env"])
    if not api_key:
        raise RuntimeError(f"Environment variable {model_cfg['api_key_env']} is not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_cfg["model_name"])
    gen_config = genai.GenerationConfig(
        temperature=model_cfg.get("temperature", 0.2),
        max_output_tokens=model_cfg.get("max_tokens", 2048),
    )
    response = model.generate_content(prompt, generation_config=gen_config)
    return response.text


_PROVIDER_FNS = {
    "anthropic":     _call_anthropic,
    "openai":        _call_openai,
    "openai_compat": _call_openai,
    "google":        _call_google,
    "ollama":        _call_ollama,
}


def make_call_llm_fn(model_cfg: dict, retries: int = 2) -> Callable[[str, str], str]:
    """Return a call_llm_fn(prompt, model_id) closure for the given config entry."""
    provider = model_cfg.get("provider", "openai")
    provider_fn = _PROVIDER_FNS.get(provider)
    if provider_fn is None:
        raise ValueError(f"Unknown provider '{provider}'. Supported: {list(_PROVIDER_FNS)}")

    def call_llm(prompt: str, _model_id: str) -> str:
        last_err = None
        for attempt in range(retries + 1):
            try:
                return provider_fn(prompt, model_cfg)
            except Exception as e:
                last_err = e
                if attempt < retries:
                    wait = 2 ** attempt
                    print(f"  [retry {attempt+1}/{retries} in {wait}s] {e}", file=sys.stderr)
                    time.sleep(wait)
        raise RuntimeError(f"All {retries+1} attempts failed: {last_err}") from last_err

    return call_llm
