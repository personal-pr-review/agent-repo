from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        normalized = base_url.rstrip("/")
        if not normalized.endswith("/v1"):
            normalized = f"{normalized}/v1"

        self._client = OpenAI(api_key=api_key, base_url=normalized, timeout=timeout_seconds)
        self._model = model

    def json_chat(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )

        content = response.choices[0].message.content or "{}"
        return self._safe_parse_json(content)

    @staticmethod
    def _safe_parse_json(raw_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}

        return {}
