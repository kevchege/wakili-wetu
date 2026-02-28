import requests
import os
from typing import Dict


from services.local_legal_engine import engine, generate_legal_answer

# determine which AI provider to use: 'gemini', 'openai', or 'local'
AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower()

# read credentials -- only one needs to be present depending on provider
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# for a self‑hosted model you can point at any HTTP URL that accepts a prompt
LOCAL_MODEL_URL = os.environ.get("LOCAL_MODEL_URL")

if AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set for Gemini provider.")
if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable not set for OpenAI provider.")
if AI_PROVIDER == "local" and not LOCAL_MODEL_URL:
    raise RuntimeError("LOCAL_MODEL_URL environment variable not set for local provider.")

# cache the selected model name so we only fetch once
_cached_model_name = None

# allow explicit override via environment when you know a valid model
# e.g. export GEMINI_MODEL_NAME="models/gemini-1.5"
MODEL_OVERRIDE = os.environ.get("GEMINI_MODEL_NAME")

def get_model_name():
    """Query the Gemini ListModels endpoint and pick a suitable model.

    Falls back to a hardcoded known-good name if detection fails.
    """
    global _cached_model_name
    # honor explicit override first
    if MODEL_OVERRIDE:
        return MODEL_OVERRIDE
    if _cached_model_name:
        return _cached_model_name
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            for m in data.get("models", []):
                name = m.get("name", "")
                if "gemini" in name.lower():
                    _cached_model_name = name
                    break
        # if none found, try any text-based model
        if not _cached_model_name and r.status_code == 200:
            data = r.json()
            for m in data.get("models", []):
                name = m.get("name", "")
                if "text-" in name.lower():
                    _cached_model_name = name
                    break
    except Exception:
        pass
    # final fallback
    if not _cached_model_name:
        # prefer a gemini flash model which is commonly available
        _cached_model_name = "models/gemini-1.5-flash"
    return _cached_model_name



def analyze_with_gemini(context: str, question: str) -> dict:
    """
    Sends legal context to Gemini for analysis.

    Returns a dict with keys 'text' and 'cites'.
    """

    prompt = f"""
You are a Kenyan legal research assistant.

IMPORTANT:
- Use ONLY the LEGAL_TEXT provided.
- Do NOT invent laws or cases.
- Explain clearly in plain English.

LEGAL_TEXT:
{context}

QUESTION:
{question}

Provide a helpful legal explanation based strictly on the text.
"""

    model = get_model_name()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 800
                }
            },
            timeout=30
        )

        # ✅ Surface API errors instead of silently failing, but provide a fallback
        if response.status_code != 200:
            # simple local summarizer based on context+question
            def _local_summarize(t):
                import re
                if not t: return ''
                s = re.split(r"(?<=[.?!])\s+", t.strip())
                if len(s) >= 2:
                    return (s[0] + ' ' + s[1]).strip()
                return (t.strip()[:400] + ('...' if len(t.strip())>400 else '')).strip()
            combined = (context + ' ' + question).strip()
            fallback = _local_summarize(combined)
            # if fallback is basically the same as the question/context,
            # return a generic note so the chat doesn't seem broken
            if fallback.strip() == combined.strip():
                fallback = "The AI service is currently unavailable; please try again later."
            return {"text": f" {fallback}", "cites": []}

        data = response.json()

        # ✅ Extract model text safely
        candidates = data.get("candidates", [])
        if not candidates:
            return {"text": "[AI returned no candidates]", "cites": []}

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return {"text": "[AI returned empty content]", "cites": []}

        text = parts[0].get("text", "").strip()

        if not text:
            return {"text": "[AI returned empty text]", "cites": []}

        return {"text": text, "cites": []}

    except requests.exceptions.Timeout:
        return {"text": "[AI request timed out]", "cites": []}

    except Exception as e:
        # network or parsing exception; provide fallback summary
        def _local_summarize(t):
            import re
            if not t: return ''
            s = re.split(r"(?<=[.?!])\s+", t.strip())
            if len(s) >= 2:
                return (s[0] + ' ' + s[1]).strip()
            return (t.strip()[:400] + ('...' if len(t.strip())>400 else '')).strip()
        combined = (context + ' ' + question).strip()
        fallback = _local_summarize(combined)
        if fallback.strip() == combined.strip():
            fallback = "The AI service is currently unavailable; please try again later."
        return {"text": f"[fallback] {fallback}", "cites": []}

# --- additional provider implementations ---


def analyze_with_local(context: str, question: str) -> dict:
    """
    Fully offline legal analysis engine.
    """

    search_query = f"{question} {context[:500]}"
    results = engine.search(search_query)

    answer, cites = generate_legal_answer(results, question)

    return {
        "text": answer,
        "cites": cites
    }

def analyze_with_openai(context: str, question: str) -> dict:
    """Call OpenAI Responses API for analysis."""
    prompt = (
        "You are a Kenyan legal research assistant.\n\n"
        f"LEGAL_TEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n"
    )
    url = "https://api.openai.com/v1/responses"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "input": prompt,
        "temperature": 0.2,
        "max_output_tokens": 800
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
        if r.status_code != 200:
            # fallback summary
            def _loc(t):
                import re
                if not t: return ''
                s = re.split(r"(?<=[.?!])\s+", t.strip())
                return (s[0] + ' ' + s[1]).strip() if len(s)>=2 else t[:400]
            f = _loc(context + ' ' + question)
            return {"text": f"[fallback] {f}", "cites": []}
        data = r.json()
        out = ""
        if "output" in data and isinstance(data["output"], list):
            for item in data["output"]:
                if isinstance(item, dict):
                    out += item.get("content", "")
                elif isinstance(item, str):
                    out += item
        if not out and "choices" in data:
            for ch in data["choices"]:
                out += ch.get("message", {}).get("content", "")
        out = out.strip()
        if not out:
            return {"text": "[OpenAI returned empty output]", "cites": []}
        return {"text": out, "cites": []}
    except Exception as e:
        return {"text": f"[OpenAI error: {e}]", "cites": []}


def analyze(context: str, question: str) -> Dict[str, any]:
    """Dispatch based on AI_PROVIDER"""
    if AI_PROVIDER == "openai":
        return analyze_with_openai(context, question)
    elif AI_PROVIDER == "local":
        return analyze_with_local(context, question)
    else:  # default to gemini
        return analyze_with_gemini(context, question)


def summarize_document(text: str) -> dict:
    """Compatibility wrapper used by routes."""
    return analyze(text, "Provide a short, clear summary.")


