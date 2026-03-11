from streamlit import json


def try_parse_json_text(text: str):
    if not isinstance(text, str):
        return None
    t = text.strip()

    if t.startswith("```"):
        lines = t.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
        t = "\n".join(lines).strip()

    try:
        return json.loads(t)
    except Exception:
        return None
