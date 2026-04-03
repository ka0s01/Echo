import json
import re

def parse_tool_call(content: str) -> dict | None:
    if not content or not content.strip():
        return None

    content = content.strip()

    # Strip markdown code fences — greedy so nested braces are captured correctly
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
    if fenced:
        content = fenced.group(1).strip()

    # Try parsing the whole content as JSON directly
    try:
        parsed = json.loads(content)
        if "name" in parsed and isinstance(parsed.get("arguments"), dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Fallback: extract the first outermost {...} block
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if "name" in parsed and isinstance(parsed.get("arguments"), dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return None