import json
import re


_FIRST_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def try_parse_json_text(text: str):
    if not isinstance(text, str):
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        match = _FIRST_JSON_OBJECT_RE.search(cleaned)
        if not match:
            return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None
