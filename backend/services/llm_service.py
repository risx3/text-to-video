"""Prompt enhancement via mlx-lm (Apple Silicon) or passthrough on other platforms."""
from __future__ import annotations

import logging

from backend.core.config import settings
from backend.core.models import get_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a creative video prompt engineer. "
    "Your task is to enhance a short user description into a detailed, cinematic prompt "
    "suitable for an AI video generation model. "
    "Output ONLY the enhanced prompt — no explanations, no prefixes, no quotes."
)


async def enhance_prompt(user_prompt: str) -> str:
    """Return an enhanced version of user_prompt using the local MLX LLM.

    Falls back to the raw prompt when:
    - ``TTV_ENABLE_LLM=false`` is set, or
    - mlx-lm is not installed (non-Apple platform), or
    - the LLM raises any error during generation.
    """
    if not settings.enable_llm:
        logger.debug("LLM enhancement disabled (TTV_ENABLE_LLM=false).")
        return user_prompt

    try:
        model, tokenizer = await get_llm()
    except Exception as exc:
        logger.warning("LLM unavailable (%s), using raw prompt.", exc)
        return user_prompt

    # get_llm returns (None, None) when mlx-lm is not installed
    if model is None or tokenizer is None:
        return user_prompt

    try:
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler
    except ImportError:
        logger.warning("mlx-lm not available — prompt enhancement skipped.")
        return user_prompt

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # Apply chat template if available
    try:
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        prompt_text = f"<|system|>{SYSTEM_PROMPT}<|user|>{user_prompt}<|assistant|>"

    try:
        sampler = make_sampler(temp=settings.llm_temp)
        enhanced = generate(
            model,
            tokenizer,
            prompt=prompt_text,
            max_tokens=settings.llm_max_tokens,
            sampler=sampler,
            verbose=False,
        )
        enhanced = enhanced.strip()
        logger.info("Prompt enhanced (first 120 chars): %s", enhanced[:120])
        return enhanced or user_prompt
    except Exception as exc:
        logger.warning("LLM generation failed (%s), using raw prompt.", exc)
        return user_prompt
