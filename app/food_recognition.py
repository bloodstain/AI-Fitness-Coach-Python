import base64
import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.config import OPENAI_API_KEY, OPENAI_VISION_MODEL


def _extract_output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    chunks: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks)


def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        normalized.append(
            {
                "name": str(item.get("name") or "未知食物"),
                "amount": float(item.get("amount") or 100),
                "unit": str(item.get("unit") or "g"),
                "calories": int(float(item.get("calories") or 0)),
                "protein_g": int(float(item.get("protein_g") or 0)),
                "carbs_g": int(float(item.get("carbs_g") or 0)),
                "fat_g": int(float(item.get("fat_g") or 0)),
                "thumb_key": str(item.get("thumb_key") or f"food-{index}"),
            }
        )
    return normalized


def recognize_food_image(image_bytes: bytes, content_type: str) -> dict[str, Any] | None:
    if not OPENAI_API_KEY:
        return None

    image_data = base64.b64encode(image_bytes).decode("utf-8")
    prompt = (
        "识别图片中的食物，估算每一种食物的重量和营养。"
        "只返回 JSON，不要 Markdown。格式："
        '{"confidence":0.86,"items":[{"name":"鸡胸肉","amount":150,'
        '"unit":"g","calories":248,"protein_g":34,"carbs_g":1,'
        '"fat_g":5,"thumb_key":"chicken"}]}。'
        "thumb_key 使用英文小写，可用 chicken/rice/broccoli/egg/salad/shrimp/beef/food。"
    )
    payload = {
        "model": OPENAI_VISION_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:{content_type};base64,{image_data}",
                        "detail": "low",
                    },
                ],
            }
        ],
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    text = _extract_output_text(data)
    if not text:
        return None

    try:
        parsed = _parse_json(text)
    except json.JSONDecodeError:
        return None

    items = _normalize_items(parsed.get("items", []))
    if not items:
        return None

    return {
        "confidence": float(parsed.get("confidence") or 0.82),
        "total_calories": sum(item["calories"] for item in items),
        "items": items,
        "source": "vision",
    }
