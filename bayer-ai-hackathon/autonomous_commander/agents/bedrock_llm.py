"""
Shared Bedrock LLM factory.
Centralizes model/region configuration so agents stay in sync.
"""

from __future__ import annotations

import os
import warnings
from langchain_aws import ChatBedrock


DEFAULT_MODEL_ID = "meta.llama3-3-70b-instruct-v1:0"


def _resolve_model_id() -> str:
    """
    Prefer an inference profile or model ID provided via environment.
    BEDROCK_MODEL_ID should be set to the inference profile ID or ARN when required.
    """
    model_id = (
        os.getenv("BEDROCK_MODEL_ID")
        or os.getenv("BEDROCK_INFERENCE_PROFILE")
        or DEFAULT_MODEL_ID
    )

    if model_id == DEFAULT_MODEL_ID:
        warnings.warn(
            "BEDROCK_MODEL_ID not set. Using default model ID which may require an "
            "inference profile and fail for on-demand invocation. "
            "Set BEDROCK_MODEL_ID to your inference profile ID/ARN if you see "
            "a ValidationException.",
            stacklevel=2,
        )

    return model_id


def _resolve_region() -> str:
    return (
        os.getenv("BEDROCK_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1"
    )


def _resolve_provider(model_id: str) -> str | None:
    provider = os.getenv("BEDROCK_PROVIDER")
    if provider:
        return provider

    if not model_id.startswith("arn:"):
        return None

    lowered = model_id.lower()
    if "anthropic." in lowered:
        return "anthropic"
    if "meta." in lowered or "llama" in lowered:
        return "meta"
    if "amazon." in lowered:
        return "amazon"
    if "cohere." in lowered:
        return "cohere"
    if "mistral." in lowered:
        return "mistral"

    return None


def get_bedrock_llm(*, max_tokens: int, temperature: float) -> ChatBedrock:
    model_id = _resolve_model_id()
    provider = _resolve_provider(model_id)

    kwargs = {"model_id": model_id, "region_name": _resolve_region()}
    if provider:
        kwargs["provider"] = provider

    return ChatBedrock(
        **kwargs,
        model_kwargs={"max_tokens": max_tokens, "temperature": temperature},
    )
