import json
from pathlib import Path
from typing import Dict, Any, Optional, List

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
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY"
    }
}

_ACTIVE_CLIENTS = {}


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

    api_key = _load_api_key(provider)

    if provider == "openai":
        if OpenAI is None: raise ImportError("OpenAI module missing.")
        client = OpenAI(api_key=api_key)
        _ACTIVE_CLIENTS["openai"] = client
        return client

    elif provider == "groq":
        if Groq is None: raise ImportError("Groq module missing.")
        client = Groq(api_key=api_key)
        _ACTIVE_CLIENTS["groq"] = client
        return client

    elif provider == "google":
        if genai is None: raise ImportError("Google GenerativeAI module missing.")
        genai.configure(api_key=api_key)
        _ACTIVE_CLIENTS["google"] = True
        return True

    else:
        raise ValueError(f"Unsupported provider client init: {provider}")


# --------------------------------------------------------------------
# 3. Main LLM Call Function (Text Generation)
# --------------------------------------------------------------------
def call_llm(prompt: str, provider: str = DEFAULT_PROVIDER, json_mode: bool = True) -> Dict[str, Any]:
    """
    Unified LLM call.
    :param json_mode: If True (default), forces JSON response.
                      If False (e.g., chat tool), returns raw text.
    """
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        return {"reply": f"ERROR: Unknown provider: {provider}", "tools": []}

    model_name = config["model"]
    raw_response_text = ""

    try:
        _get_client(provider)

        if provider == "openai":
            client = _ACTIVE_CLIENTS["openai"]

            # If json_mode=False, set response_format to None!
            resp_format = {"type": "json_object"} if json_mode else None

            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format=resp_format,
                temperature=0.7,
            )
            raw_response_text = response.choices[0].message.content

        elif provider == "groq":
            client = _ACTIVE_CLIENTS["groq"]

            # If json_mode=False, set response_format to None!
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

        elif provider == "google":
            gen_config = {"temperature": 0.7}
            if json_mode:
                gen_config["response_mime_type"] = "application/json"

            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=gen_config
            )
            response = model.generate_content(prompt)
            raw_response_text = response.text

    except Exception as e:
        return {"reply": f"CRITICAL ERROR ({provider}): {e}", "tools": []}

    # ---------------------------------------------------------
    # Processing (JSON vs RAW)
    # ---------------------------------------------------------

    # If NOT in JSON mode, the full text is the response (no parsing)
    if not json_mode:
        return {"reply": raw_response_text, "tools": []}

    # If JSON mode, parse it
    try:
        clean_text = raw_response_text.strip()
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.startswith("```"): clean_text = clean_text[3:]
        if clean_text.endswith("```"): clean_text = clean_text[:-3]

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
        # Fallback or error
        return []
    model_name = config["embedding_model"]
    _get_client(provider)
    try:
        if provider == "google":
            result = genai.embed_content(model=model_name, content=text, task_type="retrieval_document")
            return result['embedding']
        elif provider == "openai":
            client = _ACTIVE_CLIENTS["openai"]
            response = client.embeddings.create(input=[text], model=model_name)
            return response.data[0].embedding
        else:
            return []
    except Exception as e:
        print(f"Embedding error: {e}")
        return []