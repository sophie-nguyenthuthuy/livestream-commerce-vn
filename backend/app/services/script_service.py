from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ScriptVariant,
)
from app.services.dialect_prompts import SYSTEM_PROMPT, build_user_prompt

logger = get_logger(__name__)


class ScriptGenerationError(RuntimeError):
    pass


class ScriptService:
    """Generate Vietnamese livestream scripts via a self-hosted OSS LLM
    (OpenAI-compatible endpoint — Ollama in dev, vLLM/SGLang in production).

    All sensitive seller/creator copy and pricing intel stays inside the
    operator's infrastructure; the project mandates OSS, self-hostable
    models only (Qwen / Llama / DeepSeek), not managed APIs.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(self, req: ScriptGenerateRequest) -> ScriptGenerateResponse:
        user_prompt = build_user_prompt(
            dialect=req.dialect,
            intent=req.intent,
            product_name=req.product_name,
            product_category=req.product_category,
            price_band=req.price_band,
            audience_persona=req.audience_persona,
            target_duration_sec=req.target_duration_sec,
            n_variants=req.n_variants,
        )

        model, raw = await self._call_llm(user_prompt)
        variants = self._parse_variants(raw, fallback_duration=req.target_duration_sec)
        return ScriptGenerateResponse(
            dialect=req.dialect,
            intent=req.intent,
            model=model,
            variants=variants,
        )

    @staticmethod
    def prompt_hash(req: ScriptGenerateRequest) -> str:
        canonical = json.dumps(req.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    # ---- provider ----

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _call_llm(self, user_prompt: str) -> tuple[str, str]:
        """Call the configured OpenAI-compatible OSS endpoint."""
        model = self.settings.llm_model
        base_url = self.settings.llm_base_url.rstrip("/")
        headers = {"content-type": "application/json"}
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            if r.status_code >= 400:
                logger.warning("llm_call_failed", status=r.status_code, body=r.text[:500])
                raise ScriptGenerationError(
                    f"OSS LLM endpoint {r.status_code}: {r.text[:200]}"
                )
            data = r.json()
        return model, data["choices"][0]["message"]["content"]

    # ---- parsing ----

    @staticmethod
    def _parse_variants(raw: str, *, fallback_duration: int) -> list[ScriptVariant]:
        payload = _extract_json(raw)
        if not isinstance(payload, dict) or "variants" not in payload:
            raise ScriptGenerationError("model did not return a variants array")
        out: list[ScriptVariant] = []
        for v in payload["variants"]:
            out.append(
                ScriptVariant(
                    title=str(v.get("title", "")).strip()[:255] or "(untitled)",
                    body=str(v.get("body", "")).strip(),
                    estimated_duration_sec=int(
                        v.get("estimated_duration_sec") or fallback_duration
                    ),
                    tags=[str(t)[:32] for t in (v.get("tags") or [])][:8],
                )
            )
        if not out:
            raise ScriptGenerationError("model returned 0 variants")
        return out


def _extract_json(text: str) -> Any:
    """Locate the first {...} JSON object in `text`. Models sometimes wrap in prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("`").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ScriptGenerationError("no JSON object found in model response")
    return json.loads(text[start : end + 1])
