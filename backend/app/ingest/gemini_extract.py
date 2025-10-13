"""Gemini extraction wrapper for lab results."""

from app.insights.clients import extract_labs_from_media

# Re-export for convenience
__all__ = ["extract_labs_from_media"]
