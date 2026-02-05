import json
import re
import requests
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError, conlist


# ---------- 1) 定义输出结构（schema） ----------
class Caption(BaseModel):
    platform: Literal["instagram", "tiktok", "x"]
    text: str


class KeyMoment(BaseModel):
    minute: int = Field(ge=0, le=130)
    team: str
    player: Optional[str] = None
    event_type: Literal["goal", "red_card", "penalty", "other"]
    evidence: dict  # must include event_id from FEATURES
    description: str  # natural language, but must not change the facts


class ContentPack(BaseModel):
    match_id: int
    language: Literal["en", "zh"]
    titles: conlist(str, min_length=2, max_length=3)
    captions: conlist(Caption, min_length=3, max_length=3)
    summary: str
    hashtags: List[str] = []
    key_moments: conlist(KeyMoment, min_length=0, max_length=5)


# ---------- 2) 调用 Ollama ----------
def _ollama_chat(model: str, system: str, user: str, temperature: float = 0.2) -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]


# ---------- 3) 从模型输出里提取 JSON ----------
def _extract_json(text: str) -> str:
    text = text.strip()
    # strip ```json ... ```
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", text).strip()
    # find first {...}
    m = re.search(r"\{.*\}", text, flags=re.S)
    return m.group(0) if m else text


# ---------- 4) 生成 content pack（带重试与结构校验） ----------
def generate_content_pack_local(
    features: dict,
    language: str = "en",
    model: str = "llama3.1:8b",
    max_retries: int = 2,
) -> dict:
    system = (
        "You write football social media content for editors.\n"
        "Return ONLY valid JSON. No markdown. No explanations.\n"
        "Do NOT invent facts.\n"
        "Facts must come from FEATURES: teams, players, minutes, score.\n"
        "Key moments must use minute, team, player, event_type, and evidence grounded in FEATURES.\n"
        "evidence must include event_id copied from FEATURES.\n"
    )

    base_user = {
        "task": "Generate a content pack for one match.",
        "language": language,
        "features": features,
        "output_rules": {
            "titles": "2-3 short options",
            "captions": [
                {"platform": "instagram", "tone": "fun, fan-friendly"},
                {"platform": "tiktok", "tone": "punchy, energetic"},
                {"platform": "x", "tone": "concise, newsy"},
            ],
            "summary": "80-120 words",
            "key_moments": "0-5 items. Use only moments present in FEATURES. Do NOT invent facts.",
            "hashtags": "5-12 items, relevant, no spaces",
        },
        "schema_hint": {
            "match_id": "int",
            "language": "en|zh",
            "titles": "list[str] (2-3)",
            "captions": "list[{platform,text}] (exactly 3)",
            "summary": "str",
            "hashtags": "list[str]",
            "key_moments": "list[{minute,team,player,event_type,evidence,description}] (0-5)",
        },
    }

    last_error = None
    for attempt in range(max_retries + 1):
        user = dict(base_user)
        if last_error:
            user["fix_instructions"] = (
                "Your previous output failed validation. "
                "Return ONLY corrected JSON that matches the schema. "
                f"Validation error: {last_error}"
            )

        raw = _ollama_chat(
            model=model,
            system=system,
            user=json.dumps(user, ensure_ascii=False),
            temperature=0.2,
        )
        raw_json = _extract_json(raw)

        try:
            obj = json.loads(raw_json)
            pack = ContentPack.model_validate(obj)
            return pack.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)

    raise RuntimeError(f"Failed to generate valid JSON after retries. Last error: {last_error}")
