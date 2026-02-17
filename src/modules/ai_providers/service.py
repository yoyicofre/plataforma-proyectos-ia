from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.errors import bad_request
from src.core.security import User
from src.modules.agent_runs.schemas import AgentRunCreate
from src.modules.agent_runs.service import create_agent_run
from src.modules.ai_providers.schemas import (
    AiImageGenerateRequest,
    AiImageGenerateResponse,
    AiTextGenerateRequest,
    AiTextGenerateResponse,
)

PROVIDERS = {"openai", "gemini"}


def _providers_order(preference: str) -> list[str]:
    pref = preference.lower().strip()
    if pref in PROVIDERS:
        return [pref, *sorted(PROVIDERS - {pref})]
    if pref == "auto":
        return ["openai", "gemini"]
    raise bad_request("provider_preference must be one of: auto, openai, gemini")


def _estimate_text_cost(provider: str, in_tokens: int | None, out_tokens: int | None) -> float:
    input_tokens = in_tokens or 0
    output_tokens = out_tokens or 0
    if provider == "openai":
        return round(
            (input_tokens / 1000) * settings.openai_text_input_cost_per_1k
            + (output_tokens / 1000) * settings.openai_text_output_cost_per_1k,
            6,
        )
    return round(
        (input_tokens / 1000) * settings.gemini_text_input_cost_per_1k
        + (output_tokens / 1000) * settings.gemini_text_output_cost_per_1k,
        6,
    )


def _estimate_image_cost(provider: str) -> float:
    if provider == "openai":
        return round(settings.openai_image_cost_per_image, 6)
    return round(settings.gemini_image_cost_per_image, 6)


def _openai_text(req: AiTextGenerateRequest) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise bad_request("OPENAI_API_KEY is not configured")
    model = req.model_name or settings.openai_model_text
    messages: list[dict[str, Any]] = []
    if req.system_prompt:
        messages.append({"role": "system", "content": [{"type": "input_text", "text": req.system_prompt}]})
    messages.append({"role": "user", "content": [{"type": "input_text", "text": req.prompt}]})
    payload: dict[str, Any] = {"model": model, "input": messages}
    if req.temperature is not None:
        payload["temperature"] = req.temperature
    if req.max_output_tokens is not None:
        payload["max_output_tokens"] = req.max_output_tokens

    with httpx.Client(timeout=120) as client:
        res = client.post(
            f"{settings.openai_base_url}/responses",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if res.status_code >= 400:
        raise bad_request(f"OpenAI text call failed: {res.status_code} {res.text[:300]}")
    data = res.json()
    text_value = data.get("output_text")
    if not text_value:
        output = data.get("output", [])
        if output and isinstance(output, list):
            content = output[0].get("content", [])
            parts = [p.get("text", "") for p in content if p.get("text")]
            text_value = "\n".join(parts).strip()
    usage = data.get("usage", {}) or {}
    in_tokens = usage.get("input_tokens")
    out_tokens = usage.get("output_tokens")
    return {
        "provider": "openai",
        "model_name": model,
        "text": text_value or "",
        "token_input_count": in_tokens,
        "token_output_count": out_tokens,
        "cost_usd": _estimate_text_cost("openai", in_tokens, out_tokens),
    }


def _gemini_text(req: AiTextGenerateRequest) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise bad_request("GEMINI_API_KEY is not configured")
    model = req.model_name or settings.gemini_model_text
    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": req.prompt}]}],
    }
    if req.system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": req.system_prompt}]}
    if req.max_output_tokens is not None or req.temperature is not None:
        payload["generationConfig"] = {}
        if req.max_output_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = req.max_output_tokens
        if req.temperature is not None:
            payload["generationConfig"]["temperature"] = req.temperature

    with httpx.Client(timeout=120) as client:
        res = client.post(
            f"{settings.gemini_base_url}/models/{model}:generateContent",
            params={"key": settings.gemini_api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
        )
    if res.status_code >= 400:
        raise bad_request(f"Gemini text call failed: {res.status_code} {res.text[:300]}")
    data = res.json()
    candidates = data.get("candidates", [])
    text_parts: list[str] = []
    if candidates:
        parts = (candidates[0].get("content", {}) or {}).get("parts", [])
        text_parts = [p.get("text", "") for p in parts if p.get("text")]
    usage = data.get("usageMetadata", {}) or {}
    in_tokens = usage.get("promptTokenCount")
    out_tokens = usage.get("candidatesTokenCount")
    return {
        "provider": "gemini",
        "model_name": model,
        "text": "\n".join(text_parts).strip(),
        "token_input_count": in_tokens,
        "token_output_count": out_tokens,
        "cost_usd": _estimate_text_cost("gemini", in_tokens, out_tokens),
    }


def _openai_image(req: AiImageGenerateRequest) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise bad_request("OPENAI_API_KEY is not configured")
    model = req.model_name or settings.openai_model_image
    payload: dict[str, Any] = {"model": model, "prompt": req.prompt}
    if req.size:
        payload["size"] = req.size

    with httpx.Client(timeout=120) as client:
        res = client.post(
            f"{settings.openai_base_url}/images/generations",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if res.status_code >= 400:
        raise bad_request(f"OpenAI image call failed: {res.status_code} {res.text[:300]}")
    data = res.json()
    item = (data.get("data") or [{}])[0]
    return {
        "provider": "openai",
        "model_name": model,
        "mime_type": "image/png",
        "image_base64": item.get("b64_json"),
        "image_url": item.get("url"),
        "cost_usd": _estimate_image_cost("openai"),
    }


def _gemini_image(req: AiImageGenerateRequest) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise bad_request("GEMINI_API_KEY is not configured")
    model = req.model_name or settings.gemini_model_image
    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": req.prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }

    with httpx.Client(timeout=120) as client:
        res = client.post(
            f"{settings.gemini_base_url}/models/{model}:generateContent",
            params={"key": settings.gemini_api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
        )
    if res.status_code >= 400:
        raise bad_request(f"Gemini image call failed: {res.status_code} {res.text[:300]}")
    data = res.json()
    candidates = data.get("candidates", [])
    parts = ((candidates[0].get("content", {}) if candidates else {}) or {}).get("parts", [])
    inline = next((p.get("inlineData") for p in parts if p.get("inlineData")), None)
    if inline is None:
        raise bad_request("Gemini image response did not include inlineData")
    return {
        "provider": "gemini",
        "model_name": model,
        "mime_type": inline.get("mimeType"),
        "image_base64": inline.get("data"),
        "image_url": None,
        "cost_usd": _estimate_image_cost("gemini"),
    }


def generate_text(db: Session, user: User, req: AiTextGenerateRequest) -> AiTextGenerateResponse:
    errors: list[str] = []
    for provider in _providers_order(req.provider_preference):
        try:
            result = _openai_text(req) if provider == "openai" else _gemini_text(req)
            run = create_agent_run(
                db=db,
                payload=AgentRunCreate(
                    project_id=req.project_id,
                    agent_id=req.agent_id,
                    stage_id=req.stage_id,
                    provider=result["provider"],
                    model_name=result["model_name"],
                    run_status="success",
                    trigger_source="api",
                    input_payload={"prompt": req.prompt, "system_prompt": req.system_prompt},
                    output_payload={"text": result["text"]},
                    token_input_count=result.get("token_input_count"),
                    token_output_count=result.get("token_output_count"),
                    cost_usd=result.get("cost_usd"),
                    created_by_user_id=int(user.id),
                ),
            )
            return AiTextGenerateResponse(
                run_id=run.agent_run_id,
                provider=result["provider"],
                model_name=result["model_name"],
                text=result["text"],
                token_input_count=result.get("token_input_count"),
                token_output_count=result.get("token_output_count"),
                cost_usd=result.get("cost_usd"),
            )
        except Exception as exc:
            errors.append(f"{provider}: {exc}")

    failed_run = create_agent_run(
        db=db,
        payload=AgentRunCreate(
            project_id=req.project_id,
            agent_id=req.agent_id,
            stage_id=req.stage_id,
            provider=None,
            model_name=req.model_name,
            run_status="failed",
            trigger_source="api",
            input_payload={"prompt": req.prompt, "system_prompt": req.system_prompt},
            error_message=" | ".join(errors)[:1000],
            created_by_user_id=int(user.id),
        ),
    )
    raise bad_request(f"All providers failed. run_id={failed_run.agent_run_id}. errors={errors}")


def generate_image(db: Session, user: User, req: AiImageGenerateRequest) -> AiImageGenerateResponse:
    errors: list[str] = []
    for provider in _providers_order(req.provider_preference):
        try:
            result = _openai_image(req) if provider == "openai" else _gemini_image(req)
            run = create_agent_run(
                db=db,
                payload=AgentRunCreate(
                    project_id=req.project_id,
                    agent_id=req.agent_id,
                    stage_id=req.stage_id,
                    provider=result["provider"],
                    model_name=result["model_name"],
                    run_status="success",
                    trigger_source="api",
                    input_payload={"prompt": req.prompt, "size": req.size},
                    output_payload={
                        "mime_type": result.get("mime_type"),
                        "image_url": result.get("image_url"),
                        "has_image_base64": bool(result.get("image_base64")),
                    },
                    cost_usd=result.get("cost_usd"),
                    created_by_user_id=int(user.id),
                ),
            )
            return AiImageGenerateResponse(
                run_id=run.agent_run_id,
                provider=result["provider"],
                model_name=result["model_name"],
                mime_type=result.get("mime_type"),
                image_base64=result.get("image_base64"),
                image_url=result.get("image_url"),
                cost_usd=result.get("cost_usd"),
            )
        except Exception as exc:
            errors.append(f"{provider}: {exc}")

    failed_run = create_agent_run(
        db=db,
        payload=AgentRunCreate(
            project_id=req.project_id,
            agent_id=req.agent_id,
            stage_id=req.stage_id,
            provider=None,
            model_name=req.model_name,
            run_status="failed",
            trigger_source="api",
            input_payload={"prompt": req.prompt, "size": req.size},
            error_message=" | ".join(errors)[:1000],
            created_by_user_id=int(user.id),
        ),
    )
    raise bad_request(f"All providers failed. run_id={failed_run.agent_run_id}. errors={errors}")
