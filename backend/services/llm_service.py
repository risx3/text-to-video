"""Prompt enhancement via mlx-lm."""
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
    """Return an enhanced version of user_prompt using the local MLX LLM."""
    try:
        model, tokenizer = await get_llm()
    except Exception as exc:
        logger.warning("LLM unavailable (%s), using raw prompt.", exc)
        return user_prompt

    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler

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
        logger.info("Enhanced prompt: %s", enhanced[:120])
        return enhanced or user_prompt
    except Exception as exc:
        logger.warning("LLM generation failed (%s), using raw prompt.", exc)
        return user_prompt
