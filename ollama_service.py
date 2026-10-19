
import json
import urllib.error
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"
TIMEOUT_SECONDS = 25


def ask_ollama(question: str) -> str | None:
    """Return a local AI answer, or None if Ollama is unavailable."""

    question = question.strip()

    if not question or len(question) > 2000:
        return None

    payload = {
        "model": MODEL_NAME,
        "prompt": (
            "You are CampusAssist, a helpful student support assistant. "
            "Answer the student's question clearly and concisely. "
            "Return only the final answer intended for the student. "
            "Never reveal internal reasoning, planning, or analysis. "
            "You may answer general educational and study questions. "
            "Never invent college policies, fees, deadlines, exam results, "
            "attendance records, or private student information. "
            "For personal records, direct the student to their official "
            "college portal. If you do not know something, say so. "
            "Do not claim to access college systems.\n\n"
            "Return valid JSON with one key named answer containing only the final response. "
            f"Student question: {question}"
),
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": 0.3,
            "num_predict": 350,
            },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=TIMEOUT_SECONDS
        ) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result.get("response", "").strip()
       
        # Handle models that return JSON-formatted answers.
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict):
                answer = str(parsed.get("answer", "")).strip()
        except (json.JSONDecodeError, TypeError):
            pass

        return answer or None

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None
