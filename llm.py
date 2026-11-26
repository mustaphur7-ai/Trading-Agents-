"""Thin wrapper around the Anthropic Messages API."""
from anthropic import Anthropic

import config

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    return _client


def ask(system: str, user: str, max_tokens: int = 900) -> str:
    """Send one prompt and return the text reply."""
    resp = _get_client().messages.create(
        model=config.MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
