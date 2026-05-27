import json
import re
from app.rag.chatbot import get_llm, extract_text_from_content
from app.utils.logger import logger
from typing import Dict, Any, Optional

PARSER_SYSTEM_PROMPT = """You are a traffic incident parser. Your job is to analyze the user's conversational query describing a traffic incident or asking about fines, and extract the state/location context, vehicle type, and all traffic violations, along with repeat offence indicators.

You MUST return ONLY a valid JSON object matching this exact schema:
{{
  "state": "Maharashtra" | "Tamil Nadu" | null,
  "vehicle_type": "Bike" | "Scooter" | "Car" | "Auto Rickshaw" | "Truck" | "Bus" | "Commercial Vehicle" | null,
  "violations": [
    {{
      "name": "No Helmet" | "Triple Riding" | "No Seatbelt" | "Signal Jumping" | "Drunk Driving" | "Overspeeding" | "Mobile Phone Usage" | "Driving Without Insurance" | "Driving Without License" | "Wrong Parking" | "Tinted Windows",
      "repeat_offence": boolean
    }}
  ]
}}

Extraction guidelines:
1. State: Extract the state context. If a city is mentioned (e.g. Pune, Mumbai), resolve it to "Maharashtra". If Chennai is mentioned, resolve it to "Tamil Nadu".
2. Vehicle type: Resolve to "Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", or "Commercial Vehicle". If the user says "I was riding", assume "Bike" or "Scooter" unless specified. If they say "driving", assume "Car" unless specified.
3. Violations: Extract all violations that apply. For example:
   - "riding without helmet" or "no helmet" -> "No Helmet"
   - "triple riding", "three of us on a bike" -> "Triple Riding"
   - "speeding", "drove at 120kmph" -> "Overspeeding"
   - "drunk", "drinking and driving", "booze" -> "Drunk Driving"
   - "phone", "texting while driving" -> "Mobile Phone Usage"
   - "seatbelt", "driving without belt" -> "No Seatbelt"
   - "signal", "jumped signal", "red light" -> "Signal Jumping"
   - "no license", "licence" -> "Driving Without License"
   - "insurance expired" -> "Driving Without Insurance"
   - "no parking", "wrong parking" -> "Wrong Parking"
   - "tinted glass", "black film" -> "Tinted Windows"
4. Repeat offence: Look for keywords like "again", "repeat", "second time", "previously caught", "previously fined", "another time". If found for a violation, set "repeat_offence" to true, otherwise false.

Respond ONLY with the JSON object. Do NOT include any explanations, introductory text, or markdown formatting other than the JSON itself.
"""

def clean_json_response(content: str) -> Optional[Dict[str, Any]]:
    """
    Cleans raw LLM response text, stripping markdown blocks if present,
    and returns a parsed Python dictionary.
    """
    # 1. Strip markdown code block wrappers
    cleaned = content.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = cleaned
        
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to parse JSON from LLM content: {e}. Content was: {content}")
        # Try to find anything enclosed in braces as a last resort
        braces_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if braces_match:
            try:
                return json.loads(braces_match.group(1))
            except:
                pass
        return None

async def parse_violation_query(query: str, session_state: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Calls OpenAI model to parse the conversational user query into a structured dict.
    """
    logger.info(f"Parsing query: '{query}' (session_state context: {session_state})")
    
    # Enrich the prompt with session state context if available to help resolution
    context_str = f"\n\nActive Session Location Context: {session_state}" if session_state else ""
    prompt = f"{PARSER_SYSTEM_PROMPT}{context_str}\n\nUser Incident Statement: \"{query}\"\n\nJSON Output:"
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        content = extract_text_from_content(response.content)
        parsed_dict = clean_json_response(content)
        
        if parsed_dict:
            # Backfill state from session state context if LLM didn't resolve it but we have it
            if not parsed_dict.get("state") and session_state:
                parsed_dict["state"] = session_state
            logger.info(f"Successfully parsed query. Result: {parsed_dict}")
            return parsed_dict
        else:
            logger.warning("OpenAI failed to return valid JSON.")
            return None
    except Exception as e:
        logger.error(f"Error during OpenAI NLP parsing: {e}", exc_info=True)
        return None
