"""PII redaction utilities for de-identification."""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def strip_pii(text: str) -> str:
    """
    Remove PII from text blocks.
    
    Args:
        text: Input text that may contain PII
        
    Returns:
        Text with PII redacted
    """
    if not text:
        return text
    
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\(\d{3}\)\s*\d{3}[-.]?\d{4}', '[PHONE]', text)
    
    # Social Security Numbers
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    text = re.sub(r'\b\d{9}\b', '[SSN]', text)
    
    # Medical Record Numbers (common patterns)
    text = re.sub(r'\bMRN\s*:?\s*\d+\b', '[MRN]', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMedical Record\s*:?\s*\d+\b', '[MRN]', text, flags=re.IGNORECASE)
    
    # Dates of birth (various formats)
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DOB]', text)
    text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b', '[DOB]', text, flags=re.IGNORECASE)
    
    # Street addresses (basic pattern)
    text = re.sub(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', '[ADDRESS]', text, flags=re.IGNORECASE)
    
    # Names (common patterns - be conservative)
    # This is a basic pattern and may need refinement
    text = re.sub(r'\b(?:Patient|Name)\s*:?\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b', '[NAME]', text, flags=re.IGNORECASE)
    
    # Insurance information
    text = re.sub(r'\b(?:Insurance|Policy)\s*:?\s*[A-Z0-9-]+\b', '[INSURANCE]', text, flags=re.IGNORECASE)
    
    # Account numbers
    text = re.sub(r'\b(?:Account|Acct)\s*:?\s*\d+\b', '[ACCOUNT]', text, flags=re.IGNORECASE)
    
    logger.info("PII redaction completed")
    return text


def redact_lab_data(lab_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact PII from lab data structure.
    
    Args:
        lab_data: Lab data that may contain PII
        
    Returns:
        Lab data with PII redacted
    """
    redacted = lab_data.copy()
    
    # Redact text fields
    text_fields = ["notes", "comments", "description"]
    for field in text_fields:
        if field in redacted and redacted[field]:
            redacted[field] = strip_pii(str(redacted[field]))
    
    # Redact any additional metadata that might contain PII
    if "metadata" in redacted and isinstance(redacted["metadata"], dict):
        for key, value in redacted["metadata"].items():
            if isinstance(value, str):
                redacted["metadata"][key] = strip_pii(value)
    
    return redacted
