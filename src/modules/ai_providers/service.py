from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.errors import bad_request, service_unavailable
from src.core.logging import get_logger
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
logger = get_logger(__name__)


def _trim_text(value: str | None, max_chars: int) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 32].rstrip() + " [truncated]"


def _prepare_text_request(req: AiTextGenerateRequest) -> AiTextGenerateRequest:
    prompt = _trim_text(req.prompt, settings.ai_text_input_char_limit) or ""
    system_prompt = _trim_text(req.system_prompt, settings.ai_system_prompt_char_limit)

    max_output_tokens = req.max_output_tokens
    if max_output_tokens is None:
        max_output_tokens = settings.ai_text_default_max_output_tokens
    max_output_tokens = min(max_output_tokens, settings.ai_text_hard_max_output_tokens)

    return AiTextGenerateRequest(
        project_id=req.project_id,
        agent_id=req.agent_id,
        prompt=prompt,
        system_prompt=system_prompt,
        stage_id=req.stage_id,
        provider_preference=req.provider_preference,
        model_name=req.model_name,
        temperature=req.temperature,
        max_output_tokens=max_output_tokens,
    )


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


def _resolve_agent_id(db: Session, project_id: int, requested_agent_id: int | None) -> int:
    if requested_agent_id is not None:
        return int(requested_agent_id)

    project_agent = db.execute(
        text(
            """
            SELECT paa.agent_id
            FROM project_agent_assignments paa
            JOIN agent_catalog ac ON ac.agent_id = paa.agent_id
            WHERE paa.project_id = :project_id
              AND paa.assignment_status = 'active'
              AND ac.is_active = 1
            ORDER BY paa.project_agent_assignment_id DESC
            LIMIT 1
            """
        ),
        {"project_id": project_id},
    ).scalar_one_or_none()
    if project_agent is not None:
        return int(project_agent)

    any_active_agent = db.execute(
        text(
            """
            SELECT agent_id
            FROM agent_catalog
            WHERE is_active = 1
            ORDER BY agent_id
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    if any_active_agent is not None:
        return int(any_active_agent)

    raise bad_request("No active agent available. Create/activate an agent first.")


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

    try:
        with httpx.Client(timeout=settings.ai_http_timeout_seconds) as client:
            res = client.post(
                f"{settings.openai_base_url}/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise service_unavailable("OpenAI timeout: request exceeded the configured provider timeout.") from exc
    except httpx.HTTPError as exc:
        raise service_unavailable(f"OpenAI connectivity error: {exc}") from exc
    if res.status_code >= 400:
        detail = f"OpenAI text call failed: {res.status_code} {res.text[:300]}"
        if res.status_code in {408, 429} or res.status_code >= 500:
            raise service_unavailable(detail)
        raise bad_request(detail)
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

    try:
        with httpx.Client(timeout=settings.ai_http_timeout_seconds) as client:
            res = client.post(
                f"{settings.gemini_base_url}/models/{model}:generateContent",
                params={"key": settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise service_unavailable("Gemini timeout: request exceeded the configured provider timeout.") from exc
    except httpx.HTTPError as exc:
        raise service_unavailable(f"Gemini connectivity error: {exc}") from exc
    if res.status_code >= 400:
        detail = f"Gemini text call failed: {res.status_code} {res.text[:300]}"
        if res.status_code in {408, 429} or res.status_code >= 500:
            raise service_unavailable(detail)
        raise bad_request(detail)
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

    try:
        with httpx.Client(timeout=settings.ai_http_timeout_seconds) as client:
            res = client.post(
                f"{settings.openai_base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise service_unavailable("OpenAI image timeout: provider request exceeded timeout.") from exc
    except httpx.HTTPError as exc:
        raise service_unavailable(f"OpenAI image connectivity error: {exc}") from exc
    if res.status_code >= 400:
        detail = f"OpenAI image call failed: {res.status_code} {res.text[:300]}"
        if res.status_code in {408, 429} or res.status_code >= 500:
            raise service_unavailable(detail)
        raise bad_request(detail)
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

    try:
        with httpx.Client(timeout=settings.ai_http_timeout_seconds) as client:
            res = client.post(
                f"{settings.gemini_base_url}/models/{model}:generateContent",
                params={"key": settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise service_unavailable("Gemini image timeout: provider request exceeded timeout.") from exc
    except httpx.HTTPError as exc:
        raise service_unavailable(f"Gemini image connectivity error: {exc}") from exc
    if res.status_code >= 400:
        detail = f"Gemini image call failed: {res.status_code} {res.text[:300]}"
        if res.status_code in {408, 429} or res.status_code >= 500:
            raise service_unavailable(detail)
        raise bad_request(detail)
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
    prepared_req = _prepare_text_request(req)
    agent_id = _resolve_agent_id(db=db, project_id=req.project_id, requested_agent_id=req.agent_id)
    logger.info(
        "ai_text_start user_id=%s project_id=%s agent_id=%s provider_pref=%s model_override=%s prompt_len=%s system_len=%s max_output_tokens=%s",
        int(user.id),
        prepared_req.project_id,
        agent_id,
        prepared_req.provider_preference,
        prepared_req.model_name,
        len(prepared_req.prompt or ""),
        len(prepared_req.system_prompt or ""),
        prepared_req.max_output_tokens,
    )
    errors: list[str] = []
    error_statuses: list[int] = []
    for provider in _providers_order(prepared_req.provider_preference):
        try:
            logger.info(
                "ai_text_provider_attempt provider=%s project_id=%s agent_id=%s",
                provider,
                prepared_req.project_id,
                agent_id,
            )
            result = _openai_text(prepared_req) if provider == "openai" else _gemini_text(prepared_req)
            run = create_agent_run(
                db=db,
                payload=AgentRunCreate(
                    project_id=prepared_req.project_id,
                    agent_id=agent_id,
                    stage_id=prepared_req.stage_id,
                    provider=result["provider"],
                    model_name=result["model_name"],
                    run_status="success",
                    trigger_source="api",
                    input_payload={"prompt": prepared_req.prompt, "system_prompt": prepared_req.system_prompt},
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
        except HTTPException as exc:
            error_statuses.append(exc.status_code)
            logger.exception(
                "ai_text_provider_error provider=%s project_id=%s agent_id=%s status=%s error=%s",
                provider,
                prepared_req.project_id,
                agent_id,
                exc.status_code,
                str(exc),
            )
            errors.append(f"{provider}: {exc.detail}")
        except Exception as exc:
            error_statuses.append(503)
            logger.exception(
                "ai_text_provider_error provider=%s project_id=%s agent_id=%s status=503 error=%s",
                provider,
                prepared_req.project_id,
                agent_id,
                str(exc),
            )
            errors.append(f"{provider}: {exc}")

    failed_run = create_agent_run(
        db=db,
        payload=AgentRunCreate(
            project_id=prepared_req.project_id,
            agent_id=agent_id,
            stage_id=prepared_req.stage_id,
            provider=None,
            model_name=prepared_req.model_name,
            run_status="failed",
            trigger_source="api",
            input_payload={"prompt": prepared_req.prompt, "system_prompt": prepared_req.system_prompt},
            error_message=" | ".join(errors)[:1000],
            created_by_user_id=int(user.id),
        ),
    )
    logger.error(
        "ai_text_all_providers_failed project_id=%s agent_id=%s run_id=%s errors=%s",
        prepared_req.project_id,
        agent_id,
        failed_run.agent_run_id,
        errors,
    )
    if error_statuses and all(status >= 500 for status in error_statuses):
        raise service_unavailable(
            f"All providers failed due to upstream/unavailable conditions. run_id={failed_run.agent_run_id}. errors={errors}"
        )
    raise bad_request(f"All providers failed. run_id={failed_run.agent_run_id}. errors={errors}")


def generate_image(db: Session, user: User, req: AiImageGenerateRequest) -> AiImageGenerateResponse:
    agent_id = _resolve_agent_id(db=db, project_id=req.project_id, requested_agent_id=req.agent_id)
    logger.info(
        "ai_image_start user_id=%s project_id=%s agent_id=%s provider_pref=%s model_override=%s prompt_len=%s size=%s",
        int(user.id),
        req.project_id,
        agent_id,
        req.provider_preference,
        req.model_name,
        len(req.prompt or ""),
        req.size,
    )
    errors: list[str] = []
    for provider in _providers_order(req.provider_preference):
        try:
            logger.info("ai_image_provider_attempt provider=%s project_id=%s agent_id=%s", provider, req.project_id, agent_id)
            result = _openai_image(req) if provider == "openai" else _gemini_image(req)
            run = create_agent_run(
                db=db,
                payload=AgentRunCreate(
                    project_id=req.project_id,
                    agent_id=agent_id,
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
            logger.exception(
                "ai_image_provider_error provider=%s project_id=%s agent_id=%s error=%s",
                provider,
                req.project_id,
                agent_id,
                str(exc),
            )
            errors.append(f"{provider}: {exc}")

    failed_run = create_agent_run(
        db=db,
        payload=AgentRunCreate(
            project_id=req.project_id,
            agent_id=agent_id,
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
    logger.error(
        "ai_image_all_providers_failed project_id=%s agent_id=%s run_id=%s errors=%s",
        req.project_id,
        agent_id,
        failed_run.agent_run_id,
        errors,
    )
    raise bad_request(f"All providers failed. run_id={failed_run.agent_run_id}. errors={errors}")
