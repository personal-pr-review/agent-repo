from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    github_token: str
    llm_api_key: str
    llm_api_url: str
    llm_model: str

    @staticmethod
    def from_env() -> "AppConfig":
        github_token = os.getenv("GITHUB_TOKEN", "").strip()
        llm_api_key = os.getenv("LLM_API_KEY", "").strip()
        llm_api_url = os.getenv("LLM_API_URL", "https://genai-sharedservice-americas.pwc.com").strip()
        llm_model = os.getenv("LLM_MODEL", "azure.gpt-4o-mini").strip()

        missing = []
        if not github_token:
            missing.append("GITHUB_TOKEN")
        if not llm_api_key:
            missing.append("LLM_API_KEY")
        if not llm_api_url:
            missing.append("LLM_API_URL")
        if not llm_model:
            missing.append("LLM_MODEL")

        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {joined}")

        return AppConfig(
            github_token=github_token,
            llm_api_key=llm_api_key,
            llm_api_url=llm_api_url,
            llm_model=llm_model,
        )
