import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime  # Added for timestamping

# Importing external libraries
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from groq import Groq
except ImportError:
    Groq = None

# ====================================================================
# CONFIGURATION
# ====================================================================

DEFAULT_PROVIDER = "google"

PROVIDER_CONFIG = {
    "google": {
        "model": "gemini-2.0-flash",
        "embedding_model": "models/text-embedding-004",
        "env_key": "GOOGLE_API_KEY"
    },
    "openai": {
        "model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small",
        "env_key": "OPENAI_API_KEY"
    },
    # Default Groq (fallback)
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY"
    },
    # Specific Persona: LLAMA (Creative)
    "groq_llama": {
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY"
    },
    # Specific Persona: OSS (Logical/Alternative - using Mixtral)
    "groq_oss": {
        "model": "mixtral-8x7b-32768",
        "env_key": "GROQ_API_KEY"
    }
}

_ACTIVE_CLIENTS = {}


def _save_last_call(provider: str, model: str, prompt: str, response: str):
    """
    Saves the content of the last LLM call to a JSON file for debugging/monitoring purposes.
    Filename example: last_llm_call_gemini-2_0-flash.json
    """
    try:
        # Clean filename (replace slashes or colons)
        safe_model_name = model.replace("/", "_").replace(":", "_")
        filename = f"last_llm_call_{safe_model_name}.json"

        # Save to the 'b/' directory (parent of 'engine/')
        base_dir = Path(__file__).resolve().parent.parent
        file_path = base_dir / filename

        debug_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "provider": provider,
            "model": model,
            "prompt_length": len(prompt),
            "input_prompt": prompt,
            "raw_response": response
        }

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"[LLM MONITOR WARNING] Failed to save debug file: {e}")


def _load_api_key(provider: str) -> str:
    base_dir = Path(__file__).resolve().parent.parent
    token_path = base_dir.parent / "tokens" / "project_token.json"

    if not token_path.exists():
        raise RuntimeError(f"Token file not found: {token_path}")

    with token_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unknown provider configuration: {provider}")

    key_key = config["env_key"]
    api_key = data.get(key_key)

    if not api_key:
        raise RuntimeError(f"{key_key} not found in project_token.json file.")

    return api_key


def _get_client(provider: str):
    if provider in _ACTIVE_CLIENTS:
        return _ACTIVE_CLIENTS[provider]

    # Handle alias providers (groq_llama -> uses groq client logic)
    real_provider_type = "groq" if "groq" in provider else provider

    api_key = _load_api_key(provider)

    if real_provider_type == "openai":
        if OpenAI is None: raise ImportError("OpenAI module missing.")
        client = OpenAI(api_key=api_key)
        _ACTIVE_CLIENTS[provider] = client
        return client

    elif real_provider_type == "groq":
        if Groq is None: raise ImportError("Groq module missing.")
        client = Groq(api_key=api_key)
        _ACTIVE_CLIENTS[provider] = client  # Cache by alias name to be safe
        return client

    elif real_provider_type == "google":
        if genai is None: raise ImportError("Google GenerativeAI module missing.")
        genai.configure(api_key=api_key)
        _ACTIVE_CLIENTS[provider] = True
        return True

    else:
        raise ValueError(f"Unsupported provider client init: {provider}")


def call_llm(prompt: str, provider: str = DEFAULT_PROVIDER, json_mode: bool = True) -> Dict[str, Any]:
    """
    Unified LLM call.
    Supports extended provider keys (e.g., 'groq_oss').
    """
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        return {"reply": f"ERROR: Unknown provider: {provider}", "tools": []}

    model_name = config["model"]
    raw_response_text = ""

    # Determine base client type
    client_type = "groq" if "groq" in provider else provider

    try:
        _get_client(provider)

        if client_type == "openai":
            client = _ACTIVE_CLIENTS[provider]
            resp_format = {"type": "json_object"} if json_mode else None
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format=resp_format,
                temperature=0.7,
            )
            raw_response_text = response.choices[0].message.content

        elif client_type == "groq":
            client = _ACTIVE_CLIENTS[provider]
            resp_format = {"type": "json_object"} if json_mode else None
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format=resp_format,
                temperature=0.7,
                max_tokens=8192,
                top_p=1,
                stream=False
            )
            raw_response_text = completion.choices[0].message.content

        elif client_type == "google":
            gen_config = {"temperature": 0.7}
            if json_mode:
                gen_config["response_mime_type"] = "application/json"

            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=gen_config
            )
            response = model.generate_content(prompt)
            raw_response_text = response.text

        # --- MONITORING: SAVE RAW CALL ---
        _save_last_call(provider, model_name, prompt, raw_response_text)

    except Exception as e:
        return {"reply": f"CRITICAL ERROR ({provider}): {e}", "tools": []}

    # Processing (JSON vs RAW)
    if not json_mode:
        return {"reply": raw_response_text, "tools": []}

    try:
        clean_text = raw_response_text.strip()
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.startswith("```"): clean_text = clean_text[3:]
        if clean_text.endswith("```"): clean_text = clean_text[:-3]

        # --- FIX: SANITIZE COMMON LLM JSON ERRORS ---
        # LLMs often use \' inside double quotes, which is invalid JSON.
        # We replace \' with ' to fix parsing errors.
        clean_text = clean_text.replace(r"\'", "'")

        data = json.loads(clean_text)

        if isinstance(data, list):
            data = data[0] if len(data) > 0 and isinstance(data[0], dict) else {"reply": str(data), "tools": []}
        if not isinstance(data, dict):
            data = {"reply": str(data), "tools": []}

    except json.JSONDecodeError as e:
        return {"reply": f"Error parsing JSON response: {e}\n{raw_response_text}", "tools": []}

    if "reply" not in data: data["reply"] = ""
    if "tools" not in data or data["tools"] is None: data["tools"] = []

    return data


def get_embedding(text: str, provider: str = DEFAULT_PROVIDER) -> List[float]:
    text = (text or "").strip()
    if not text: return []
    config = PROVIDER_CONFIG.get(provider)
    if not config or "embedding_model" not in config:
        return []
    model_name = config["embedding_model"]
    _get_client(provider)
    try:
        if provider == "google":
            result = genai.embed_content(model=model_name, content=text, task_type="retrieval_document")
            return result['embedding']
        elif provider == "openai":
            client = _ACTIVE_CLIENTS[provider]
            response = client.embeddings.create(input=[text], model=model_name)
            return response.data[0].embedding
        else:
            return []
    except Exception as e:
        print(f"Embedding error: {e}")
        return []