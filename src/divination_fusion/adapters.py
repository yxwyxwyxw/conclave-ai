from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from json import JSONDecodeError
from typing import Any, Callable, Optional

import httpx


class AdapterError(RuntimeError):
    pass


@dataclass
class ModelRequest:
    provider: str
    model: str
    role: str
    system_name: str
    system_prompt: str
    user_prompt: str
    schema_name: str
    runtime_constraints: dict[str, Any] = field(default_factory=dict)
    api_key: Optional[str] = None


@dataclass
class StructuredRoleResponse:
    provider: str
    model: str
    schema_name: str
    payload: dict[str, Any]
    raw_text: str
    attempts: int


Validator = Callable[[dict[str, Any]], dict[str, Any]]


def _validate_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AdapterError(f"{field_name} 必须是字符串数组。")
    return value


def _normalize_string_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = item.strip()
        if not text or text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    return normalized


def validate_analyzer_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload.get("summary"), str) or not payload["summary"].strip():
        raise AdapterError("summary 必须是非空字符串。")
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise AdapterError("claims 必须是非空数组。")
    normalized_claims: list[dict[str, Any]] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise AdapterError(f"claims[{index}] 必须是对象。")
        for key in ("dimension", "statement", "claim_type", "basis_type", "scope"):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise AdapterError(f"claims[{index}].{key} 必须是非空字符串。")
        evidence = _validate_string_list(claim.get("evidence"), f"claims[{index}].evidence")
        uncertainty_reasons = _validate_string_list(
            claim.get("uncertainty_reasons"),
            f"claims[{index}].uncertainty_reasons",
        )
        required_inputs = _validate_string_list(
            claim.get("required_inputs"),
            f"claims[{index}].required_inputs",
        )
        qualifiers = _validate_string_list(claim.get("qualifiers"), f"claims[{index}].qualifiers")
        depends_on = _validate_string_list(claim.get("depends_on"), f"claims[{index}].depends_on")
        normalized_claims.append(
            {
                "dimension": claim["dimension"].strip(),
                "statement": claim["statement"].strip(),
                "claim_type": claim["claim_type"].strip(),
                "basis_type": claim["basis_type"].strip(),
                "basis_value": str(claim.get("basis_value", "")).strip() or None,
                "scope": claim["scope"].strip(),
                "evidence": evidence,
                "uncertainty_reasons": uncertainty_reasons,
                "required_inputs": required_inputs,
                "qualifiers": qualifiers,
                "depends_on": depends_on,
            }
        )
    warnings = _validate_string_list(payload.get("warnings"), "warnings")
    return {
        "summary": payload["summary"].strip(),
        "claims": normalized_claims,
        "warnings": warnings,
    }


def validate_battler_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("stance", "response"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise AdapterError(f"{key} 必须是非空字符串。")
    public_response = payload.get("public_response")
    if public_response is not None and (not isinstance(public_response, str) or not public_response.strip()):
        raise AdapterError("public_response 必须是非空字符串或 null。")
    summary_hint = payload.get("summary_hint")
    if summary_hint is not None and (not isinstance(summary_hint, str) or not summary_hint.strip()):
        raise AdapterError("summary_hint 必须是非空字符串或 null。")
    supported_claim_ids = _normalize_string_list(
        _validate_string_list(payload.get("supported_claim_ids"), "supported_claim_ids")
    )
    conceded_points = _normalize_string_list(
        _validate_string_list(payload.get("conceded_points"), "conceded_points")
    )
    still_disputed_points = _normalize_string_list(
        _validate_string_list(payload.get("still_disputed_points"), "still_disputed_points")
    )
    argument_points = _normalize_string_list(
        _validate_string_list(payload.get("argument_points"), "argument_points")
    )
    new_argument_points = _normalize_string_list(
        _validate_string_list(payload.get("new_argument_points"), "new_argument_points")
    )
    stop_signal = payload.get("stop_signal")
    if not isinstance(stop_signal, bool):
        raise AdapterError("stop_signal 必须是布尔值。")
    response = payload["response"].strip()
    public_text = public_response.strip() if isinstance(public_response, str) else response
    summary_text = summary_hint.strip() if isinstance(summary_hint, str) else public_text
    return {
        "stance": payload["stance"].strip(),
        "response": response,
        "public_response": public_text,
        "supported_claim_ids": supported_claim_ids,
        "conceded_points": conceded_points,
        "still_disputed_points": still_disputed_points,
        "argument_points": argument_points,
        "new_argument_points": new_argument_points,
        "summary_hint": summary_text,
        "stop_signal": stop_signal,
    }


def validate_judge_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("disposition", "rationale"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise AdapterError(f"{key} 必须是非空字符串。")
    favored_system = payload.get("favored_system")
    if favored_system is not None and not isinstance(favored_system, str):
        raise AdapterError("favored_system 必须是字符串或 null。")
    return {
        "disposition": payload["disposition"].strip(),
        "favored_system": favored_system.strip() if isinstance(favored_system, str) else None,
        "rationale": payload["rationale"].strip(),
        "conditions": _validate_string_list(payload.get("conditions"), "conditions"),
        "cited_claim_ids": _validate_string_list(payload.get("cited_claim_ids"), "cited_claim_ids"),
    }


def validate_plain_text_payload(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise AdapterError("text 必须是非空字符串。")
    return {"text": text.strip()}


VALIDATORS: dict[str, Validator] = {
    "analyzer": validate_analyzer_payload,
    "battler": validate_battler_payload,
    "judge": validate_judge_payload,
    "plain_text": validate_plain_text_payload,
}


def validator_for(schema_name: str) -> Validator:
    try:
        return VALIDATORS[schema_name]
    except KeyError as exc:
        raise AdapterError(f"未知 schema: {schema_name}") from exc


class ModelAdapter(ABC):
    provider_name: str

    def generate(self, request: ModelRequest) -> StructuredRoleResponse:
        if request.schema_name == "plain_text":
            if request.provider != "fake" and not request.api_key:
                raise AdapterError(f"{request.provider} 当前缺少可用 API key。")
            raw_text = self._call_model(request, correction_prompt=None)
            text = raw_text.strip()
            if not text:
                raise AdapterError(f"{request.provider}/{request.model} 返回了空文本。")
            return StructuredRoleResponse(
                provider=request.provider,
                model=request.model,
                schema_name=request.schema_name,
                payload={"text": text},
                raw_text=raw_text,
                attempts=1,
            )
        validator = validator_for(request.schema_name)
        if request.provider != "fake" and not request.api_key:
            raise AdapterError(f"{request.provider} 当前缺少可用 API key。")
        attempts = 0
        error_messages: list[str] = []
        correction_prompt: Optional[str] = None

        while attempts < 3:
            attempts += 1
            raw_text = self._call_model(request, correction_prompt=correction_prompt)
            try:
                payload = json.loads(_extract_json_object(raw_text))
                normalized = validator(payload)
                return StructuredRoleResponse(
                    provider=request.provider,
                    model=request.model,
                    schema_name=request.schema_name,
                    payload=normalized,
                    raw_text=raw_text,
                    attempts=attempts,
                )
            except (AdapterError, JSONDecodeError) as exc:
                error_messages.append(str(exc))
                correction_prompt = (
                    "上一轮输出未通过 JSON 校验。"
                    f"错误：{error_messages[-1]}。"
                    "请只返回一个合法 JSON 对象，不要输出 markdown、代码块或额外说明。"
                )

        raise AdapterError(
            f"{request.provider}/{request.model} 在 {request.schema_name} 角色下连续 3 次未返回合法 JSON。"
        )

    @abstractmethod
    def _call_model(self, request: ModelRequest, *, correction_prompt: Optional[str]) -> str:
        raise NotImplementedError


class OpenAIAdapter(ModelAdapter):
    provider_name = "openai"

    def _call_model(self, request: ModelRequest, *, correction_prompt: Optional[str]) -> str:
        return _call_openai_compatible_chat_completion(
            url="https://api.openai.com/v1/chat/completions",
            request=request,
            correction_prompt=correction_prompt,
            auth_headers={
                "Authorization": f"Bearer {request.api_key}",
            },
            provider_label="OpenAI",
            extra_payload={},
        )


class DeepSeekAdapter(ModelAdapter):
    provider_name = "deepseek"

    def _call_model(self, request: ModelRequest, *, correction_prompt: Optional[str]) -> str:
        return _call_openai_compatible_chat_completion(
            url="https://api.deepseek.com/v1/chat/completions",
            request=request,
            correction_prompt=correction_prompt,
            auth_headers={
                "Authorization": f"Bearer {request.api_key}",
            },
            provider_label="DeepSeek",
            extra_payload={},
        )


class OpenRouterAdapter(ModelAdapter):
    provider_name = "openrouter"

    def _call_model(self, request: ModelRequest, *, correction_prompt: Optional[str]) -> str:
        return _call_openai_compatible_chat_completion(
            url="https://openrouter.ai/api/v1/chat/completions",
            request=request,
            correction_prompt=correction_prompt,
            auth_headers={
                "Authorization": f"Bearer {request.api_key}",
                "HTTP-Referer": "https://conclave-ai.local",
                "X-OpenRouter-Title": "divination-fusion",
            },
            provider_label="OpenRouter",
            extra_payload={"max_tokens": 4096, "reasoning": {"enabled": False}},
        )


def _call_openai_compatible_chat_completion(
    *,
    url: str,
    request: ModelRequest,
    correction_prompt: Optional[str],
    auth_headers: dict[str, str],
    provider_label: str,
    extra_payload: dict[str, Any],
) -> str:
    messages = [
        {"role": "system", "content": request.system_prompt},
        {"role": "user", "content": request.user_prompt},
    ]
    if correction_prompt:
        messages.append({"role": "user", "content": correction_prompt})
    payload = {
        "model": request.model,
        "messages": messages,
        "temperature": 0.2,
        **extra_payload,
    }
    if request.schema_name != "plain_text":
        payload["response_format"] = {"type": "json_object"}
    response = _post_json(
        url,
        payload,
        headers={
            "Content-Type": "application/json",
            **auth_headers,
        },
    )
    try:
        msg = response["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning") or ""
        if not content:
            raise AdapterError(f"{provider_label} 返回了空文本。")
        return content
    except (KeyError, IndexError, TypeError) as exc:
        raise AdapterError(f"{provider_label} 返回结构异常。") from exc


class AnthropicAdapter(ModelAdapter):
    provider_name = "anthropic"

    def _call_model(self, request: ModelRequest, *, correction_prompt: Optional[str]) -> str:
        prompt = request.user_prompt
        if correction_prompt:
            prompt = f"{prompt}\n\n{correction_prompt}"
        payload = {
            "model": request.model,
            "max_tokens": 1600,
            "temperature": 0.2,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = _post_json(
            "https://api.anthropic.com/v1/messages",
            payload,
            headers={
                "x-api-key": request.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        try:
            content = response["content"]
            text_parts = [item["text"] for item in content if item.get("type") == "text"]
            return "\n".join(text_parts)
        except (KeyError, TypeError) as exc:
            raise AdapterError("Anthropic 返回结构异常。") from exc


class FakeAdapter(ModelAdapter):
    provider_name = "fake"

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = list(responses or [])

    def _call_model(self, request: ModelRequest, *, correction_prompt: Optional[str]) -> str:
        if self._responses:
            return self._responses.pop(0)
        if request.schema_name == "plain_text":
            if request.role == "analyzer":
                return (
                    f"【结论】\n{request.system_name} 对当前问题给出了一版保守分析。\n\n"
                    "【分析】\n现有资料允许先给出方向性判断，但仍需结合边界理解。"
                )
            if request.role == "battler":
                return f"{request.system_name} 围绕当前争点继续坚持自己的解释，并回应了对方上一轮的说法。"
            return (
                "【当前状态】\n结束\n\n"
                "【裁判意见】\n当前分歧已经足够清楚，可以进入终局裁决。"
            )
        if request.schema_name == "analyzer":
            return json.dumps(
                {
                    "summary": f"{request.system_name} 分析完成。",
                    "warnings": [],
                    "claims": [
                        {
                            "dimension": "career",
                            "statement": f"{request.system_name} 认为事业维度存在明确倾向。",
                            "claim_type": "trend",
                            "basis_type": "mock",
                            "basis_value": request.system_name,
                            "scope": "issue",
                            "evidence": ["mock evidence"],
                            "uncertainty_reasons": [],
                            "required_inputs": [],
                            "qualifiers": ["fake"],
                            "depends_on": [],
                        }
                    ],
                },
                ensure_ascii=False,
            )
        if request.schema_name == "battler":
            return json.dumps(
                {
                    "stance": "maintain",
                    "response": f"{request.system_name} 保持原判断。",
                    "public_response": f"{request.system_name} 的公开回应：保持原判断。",
                    "supported_claim_ids": ["mock-claim"],
                    "conceded_points": [],
                    "still_disputed_points": ["仍有争议"],
                    "argument_points": ["维持原判断"],
                    "new_argument_points": [],
                    "summary_hint": f"{request.system_name} 继续坚持原判断。",
                    "stop_signal": False,
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "disposition": "conditional",
                "favored_system": request.system_name or "bazi",
                "rationale": "fake judge rationale",
                "conditions": ["fake condition"],
                "cited_claim_ids": ["mock-claim"],
            },
            ensure_ascii=False,
        )


class AdapterRegistry:
    def __init__(self, adapters: Optional[dict[str, ModelAdapter]] = None) -> None:
        self._adapters = adapters or {
            "openai": OpenAIAdapter(),
            "deepseek": DeepSeekAdapter(),
            "openrouter": OpenRouterAdapter(),
            "anthropic": AnthropicAdapter(),
            "fake": FakeAdapter(),
        }

    def register(self, provider: str, adapter: ModelAdapter) -> None:
        self._adapters[provider] = adapter

    def get(self, provider: str) -> ModelAdapter:
        try:
            return self._adapters[provider]
        except KeyError as exc:
            raise AdapterError(f"不支持的 provider: {provider}") from exc


def _post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str]) -> dict[str, Any]:
    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:500]
        raise AdapterError(f"模型接口调用失败: {exc.response.status_code} {body}") from exc
    except httpx.RequestError as exc:
        raise AdapterError(f"模型接口调用失败: {exc}") from exc


def _extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise JSONDecodeError("No JSON object found", text, 0)
    return text[start : end + 1]
