"""Gemini client wrapper for vision and text operations."""

import json
import logging
from typing import Dict, Any, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


def ensure_live() -> None:
    """Perform minimal handshake with Gemini API to verify connectivity."""
    try:
        # List available models to verify API key
        models = list(genai.list_models())
        if not models:
            raise Exception("No models available")
        
        # Try a simple text generation
        model = genai.GenerativeModel(settings.gemini_model_text)
        response = model.generate_content("Hello")
        if not response.text:
            raise Exception("No response from Gemini")
            
        logger.info("Gemini API handshake successful")
        
    except Exception as e:
        logger.error(f"Gemini API handshake failed: {e}")
        raise Exception(f"Gemini API verification failed: {e}")


def extract_labs_from_media(file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """
    Extract lab results from image/PDF using Gemini multimodal.
    
    Args:
        file_bytes: Raw file content
        mime_type: MIME type of the file
        
    Returns:
        Dictionary with extracted lab results
    """
    try:
        # Load the vision extraction prompt
        prompt_template = _load_vision_prompt()
        
        # Create the model
        model = genai.GenerativeModel(settings.gemini_model_vision)
        
        # Prepare content parts
        content_parts = [
            {
                "mime_type": mime_type,
                "data": file_bytes
            },
            {
                "text": prompt_template
            }
        ]
        
        # Generate content with safety settings
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        response = model.generate_content(
            content_parts,
            safety_settings=safety_settings
        )
        
        if not response.text:
            raise Exception("No response from Gemini")
        
        # Parse the JSON response
        extracted_data = _parse_gemini_response(response.text)
        
        logger.info(f"Successfully extracted {len(extracted_data.get('labs', []))} lab results")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Failed to extract labs from media: {e}")
        raise Exception(f"Lab extraction failed: {e}")


def generate_chat_response(prompt: str) -> str:
    """
    Generate a chat response using Gemini.
    
    Args:
        prompt: The full prompt for the AI
        
    Returns:
        AI-generated response
    """
    try:
        # Create the model
        model = genai.GenerativeModel(settings.gemini_model_text)
        
        response = model.generate_content(prompt)
        
        if not response.text:
            raise Exception("No response from Gemini")
        
        logger.info("Successfully generated chat response")
        return response.text
        
    except Exception as e:
        logger.error(f"Failed to generate chat response: {e}")
        raise Exception(f"Chat response generation failed: {e}")


def summarize_clinician(deidentified_json: Dict[str, Any]) -> str:
    """
    Generate a clinical summary from deidentified lab data.
    
    Args:
        deidentified_json: Deidentified lab results and insights
        
    Returns:
        Markdown-formatted clinical summary
    """
    try:
        # Load the clinician summary prompt
        prompt_template = _load_clinician_prompt()
        
        # Create the model
        model = genai.GenerativeModel(settings.gemini_model_text)
        
        # Prepare the prompt with data
        prompt = prompt_template.format(
            lab_data=json.dumps(deidentified_json, indent=2)
        )
        
        response = model.generate_content(prompt)
        
        if not response.text:
            raise Exception("No response from Gemini")
        
        logger.info("Successfully generated clinical summary")
        return response.text
        
    except Exception as e:
        logger.error(f"Failed to generate clinical summary: {e}")
        raise Exception(f"Clinical summary generation failed: {e}")


def _load_vision_prompt() -> str:
    """Load the vision extraction prompt template."""
    try:
        with open("prompts/vision_extract_labs.md.j2", "r") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback prompt if file not found
        return """
You are a medical lab result extraction specialist. Analyze the provided image/PDF and extract all lab results.

Return ONLY a JSON object with this exact structure:
{
  "labs": [
    {
      "analyte": "string (normalized name like 'LDL Cholesterol')",
      "value": number,
      "unit": "string (e.g., 'mg/dL', 'mmol/L')",
      "observed_at": "YYYY-MM-DD (ISO date or upload date if not found)",
      "loinc_code": "string (if identifiable, otherwise null)",
      "ref_low": number (if shown, otherwise null),
      "ref_high": number (if shown, otherwise null)
    }
  ],
  "notes": "string (any additional context)",
  "confidence": number (0.0-1.0)
}

IMPORTANT:
- Normalize analyte names (e.g., "LDL-C" → "LDL Cholesterol")
- Use ISO date format or current date if not found
- Do NOT include any PII (names, emails, DOB, addresses)
- If you see PII, redact it completely
- Be conservative with confidence scores
- Return valid JSON only, no other text
"""


def _load_clinician_prompt() -> str:
    """Load the clinician summary prompt template."""
    try:
        with open("prompts/clinician_summary.md.j2", "r") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback prompt if file not found
        return """
You are a clinical assistant. Generate a professional summary of the following lab results and insights.

Lab Data:
{lab_data}

Provide a structured summary with these sections:

## Key Trends
- Highlight significant patterns or changes

## Flagged Risks  
- List any values outside normal ranges
- Note any concerning trends

## Suggested Next Steps
- Recommend follow-up actions
- Indicate urgency levels

## Data Used
- List the specific lab results analyzed

**Advisory Notice:** This summary is for informational purposes only and is not a substitute for professional medical diagnosis or treatment.
"""


def _parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parse Gemini response and extract JSON."""
    try:
        # Try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in response")
        
        json_str = response_text[start_idx:end_idx]
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("Response is not a dictionary")
        
        if "labs" not in data:
            raise ValueError("Missing 'labs' field")
        
        if not isinstance(data["labs"], list):
            raise ValueError("'labs' field is not a list")
        
        # Set default confidence if missing
        if "confidence" not in data:
            data["confidence"] = 0.8
        
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        # Try to repair common JSON issues
        try:
            # Remove trailing commas
            repaired = response_text.replace(',}', '}').replace(',]', ']')
            start_idx = repaired.find('{')
            end_idx = repaired.rfind('}') + 1
            json_str = repaired[start_idx:end_idx]
            return json.loads(json_str)
        except:
            raise ValueError(f"Failed to parse JSON response: {e}")
    except Exception as e:
        logger.error(f"Response parsing error: {e}")
        raise ValueError(f"Failed to parse response: {e}")
