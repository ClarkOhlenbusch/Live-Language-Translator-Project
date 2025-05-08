import openai
import os
import logging
import json
from dotenv import load_dotenv
import asyncio

load_dotenv() # Load environment variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI async client
client = None
if OPENAI_API_KEY:
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        logging.info("OpenAI client initialized successfully.")
        # Note: No simple usage check available like DeepL
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
        client = None
else:
    logging.warning("OPENAI_API_KEY not found in .env file. LLM suggestions will fail.")

async def get_llm_suggestions(
    english_text: str, 
    user_settings: dict = None, 
    detected_language: str = None,
    history: list = None
) -> list[dict[str, str]] | None:
    """
    Gets reply suggestions based on English text, considering user settings and detected language.
    
    Args:
        english_text: The English translation of the original text
        user_settings: User settings including conversationContext and personalInfo
        detected_language: The detected language code from DeepL (e.g., "EN", "ES", "FR")
        history: A list of previous conversation turns (dicts with 'speaker', 'original', 'english').
        
    Returns:
        A list of suggestion objects with 'original' and 'english' fields, or None on error
    """
    if not client:
        logging.error("OpenAI client is not initialized. Cannot get suggestions.")
        return None
    if not english_text or not english_text.strip():
        return [] # Return empty list for empty input
    
    # Use provided settings or default values
    if user_settings is None:
        user_settings = {}
    
    conversation_context = user_settings.get("conversationContext", "Casual conversation with a friend.")
    personal_info = user_settings.get("personalInfo", "")
    response_language = user_settings.get("responseLanguage", "detected")
    user_name = user_settings.get("userName", "User")
    
    # Format conversation history for the prompt
    history_string = ""
    if history:
        history_string = "\n\nPREVIOUS CONVERSATION TURNS (for context):\n"
        # Iterate through turns, using English for the LLM prompt context
        for turn in history:
            speaker = turn.get('speaker', 'Unknown')
            # Use English if available, otherwise original. Ensure text exists.
            text_for_llm = turn.get('english', '').strip() or turn.get('original', '').strip()
            if text_for_llm:
                history_string += f"{speaker}: {text_for_llm}\n"
    
    # Map DeepL language codes to full language names
    language_map = {
        "EN": "English",
        "DE": "German",
        "FR": "French",
        "ES": "Spanish",
        "IT": "Italian",
        "NL": "Dutch",
        "PL": "Polish",
        "PT": "Portuguese",
        "RU": "Russian",
        "JA": "Japanese",
        "ZH": "Chinese",
        "BG": "Bulgarian",
        "CS": "Czech",
        "DA": "Danish",
        "ET": "Estonian",
        "FI": "Finnish",
        "EL": "Greek",
        "HU": "Hungarian",
        "LV": "Latvian",
        "LT": "Lithuanian",
        "RO": "Romanian",
        "SK": "Slovak",
        "SL": "Slovenian",
        "SV": "Swedish"
    }
    
    # Get full language name if available
    language_name = language_map.get(detected_language, detected_language if detected_language else "unknown")
    
    # Determine if responses should match the detected language
    respond_in_detected = response_language == "detected" and detected_language and detected_language != "EN"

    # Define the persona, context, and task for the LLM (Revised for conversational nuance)
    system_prompt = f"""
You are {user_name}. Your persona, background, and personal details are defined in the USER CONTEXT. 
Your task is to generate 2-3 distinct and varied plausible things that {user_name} could say next in the conversation, based on what the other person just said (provided in the user prompt).
You must respond *as* {user_name}, drawing heavily upon the USER CONTEXT, CONVERSATION CONTEXT, and PREVIOUS CONVERSATION TURNS.
If the USER CONTEXT mentions specific preferences, facts, or a particular background (e.g., being a CS major), your responses MUST reflect this.

Generate natural conversational replies. These could be answers, follow-up questions, acknowledgements, or related comments. 
Avoid simply repeating the input phrase/question. If the input was a question, your suggestions should generally be relevant answers or related follow-up interactions from {user_name}'s perspective.

Example Interactions:
1. If USER CONTEXT says "I am a CS major at UMB" and the input is "Tell me about your studies?", good responses *as {user_name}* might be:
   - {{{{ \"original\": \"It's challenging but rewarding. I'm really enjoying my algorithms course this semester.\", \"english\": \"...\" }}}}
   - {{{{ \"original\": \"Mainly software development. It's pretty intense! What field are you in? \", \"english\": \"...\" }}}}
2. If input is "That sounds interesting.", good responses *as {user_name}* might be:
   - {{{{ \"original\": \"Thanks! It definitely keeps me busy.\", \"english\": \"...\" }}}}
   - {{{{ \"original\": \"Yeah? What part caught your attention? \", \"english\": \"...\" }}}}
   - {{{{ \"original\": \"It has its moments!\", \"english\": \"...\" }}}}
3. If input is "I just got back from hiking.", and USER CONTEXT mentions enjoying hiking, good responses *as {user_name}* might be:
   - {{{{ \"original\": \"Oh nice! Where did you go? \", \"english\": \"...\" }}}}
   - {{{{ \"original\": \"Awesome, I love hiking too. Find any good trails? \", \"english\": \"...\" }}}}

Do NOT act as a generic assistant. Embody {user_name}.

USER CONTEXT:
{personal_info}

CONVERSATION CONTEXT:
{conversation_context}
{history_string}

BEFORE YOU RESPOND:
Use this test: "Does the last thing said invite a response?"

Respond if:
- It's a direct question (e.g., “Where did you grow up?”)
- It's a personal statement clearly inviting engagement (e.g., “I went to Japan last summer” in the middle of a story)
- It's a continuation of a prior topic or exchange where the other person seems to expect input

Do NOT respond if:
- The person is just acknowledging you (e.g., “okay”, “got it”, “of course”)
- The message is a statement with no conversational hook or context (e.g., “It’s sunny today” out of nowhere)

Context matters: You must consider the last 5–10 lines of the conversation before deciding if a reply is natural. If you’re unsure, it’s better to say nothing (return `[]`).

{{"Responses should be in {language_name} to match the detected language. If so, ensure the \"original\" field is in {language_name} and the \"english\" field is its English translation." if respond_in_detected else "Responses should be in English. Both \"original\" and \"english\" fields should contain the same English text."}}

Output Format:
Output ONLY a valid JSON list of 2-3 distinct objects, where each object has keys 'original' and 'english'.
Example: [{{ \"original\": \"Oh, dove sei andato? \", \"english\": \"Oh, where did you go? \"}}, {{ \"original\": \"Fantastico, anch\'io amo fare trekking. Hai trovato bei sentieri? \", \"english\": \"Awesome, I love hiking too. Find any good trails? \"}}]
"""
    
    # The user_prompt now represents what the *other person* said
    user_prompt = f"What was said (English translation): \"{english_text}\""

    # Define the model to use
    model_name = "gpt-4o-mini"

    try:
        logging.debug(f"Sending prompt to {model_name} for text: {english_text}")
        logging.debug(f"Using system prompt: {system_prompt}")
        
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7, # Slightly higher temperature for more variation
            max_tokens=150,  # Allow more tokens for multilingual responses
            response_format={ "type": "json_object" } # Request JSON output
        )
        
        content = response.choices[0].message.content
        logging.debug(f"Received raw response from {model_name}: {content}")

        if content:
            try:
                # Parse the JSON response
                parsed_response = json.loads(content)
                
                suggestions_list = [] # Initialize an empty list

                # Handle if the response is a single dictionary
                if isinstance(parsed_response, dict) and 'original' in parsed_response and 'english' in parsed_response:
                    logging.debug("LLM returned a single dictionary, wrapping in a list.")
                    suggestions_list = [parsed_response] # Wrap the single dict in a list
                
                # Handle if the response is already a list
                elif isinstance(parsed_response, list) and all(
                    isinstance(item, dict) and 'original' in item and 'english' in item 
                    for item in parsed_response
                ):
                    suggestions_list = parsed_response # Use the list directly
                
                # Handle backwards compatibility with old format
                elif isinstance(parsed_response, dict) and 'italian' in parsed_response and 'english' in parsed_response:
                    # Convert from old format to new format
                    logging.debug("LLM returned the old format (italian), converting to new format (original).")
                    suggestions_list = [{"original": parsed_response["italian"], "english": parsed_response["english"]}]
                
                # Handle backwards compatibility with old format list
                elif isinstance(parsed_response, list) and all(
                    isinstance(item, dict) and 'italian' in item and 'english' in item 
                    for item in parsed_response
                ):
                    # Convert from old format to new format
                    logging.debug("LLM returned the old format list (italian), converting to new format (original).")
                    suggestions_list = [{"original": item["italian"], "english": item["english"]} for item in parsed_response]
                
                # Handle unexpected formats
                else:
                    logging.warning(f"LLM response JSON was not the expected format: {content}")
                    return [] # Return empty list for unexpected formats
                
                # Limit to max 3 suggestions and return
                return suggestions_list[:3]

            except json.JSONDecodeError as json_err:
                logging.error(f"Failed to parse JSON response from LLM: {json_err}\nRaw content: {content}")
                return None # Indicate failure to parse
        else:
            logging.warning("Received empty content from LLM.")
            return []

    except openai.APIError as e:
        logging.error(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error getting LLM suggestions: {e}", exc_info=True)
        return None

# Example usage (for testing this module directly)
async def main():
    test_phrases = [
        "It's a mandatory stop for art lovers.",
        "And enjoy the breathtaking view",
        "What time does the museum close?"
    ]
    
    # Example settings
    test_settings = {
        "conversationContext": "Travel conversation in Italy.",
        "personalInfo": "My name is Alex. I am a tourist visiting Rome for the first time. I speak English and a bit of Spanish.",
        "responseLanguage": "detected",
        "userName": "Alex"
    }
    
    # Add dummy history for testing if needed
    test_history = [
        {"speaker": "Friend", "original": "Ciao Alex, come stai?", "english": "Hi Alex, how are you?"},
        {"speaker": "Alex", "original": "Sto bene, grazie! E tu?", "english": "I am well, thank you! And you?"}
    ]
    
    for phrase in test_phrases:
        print(f"\n--- Testing with: '{phrase}' ---")
        # Test with Italian as the detected language
        suggestions = await get_llm_suggestions(phrase, test_settings, "IT", history=test_history)
        if suggestions is not None:
            print(f"Suggestions (with Italian detected): {suggestions}")
        else:
            print("Failed to get suggestions.")
        
        # Test with English as the detected language
        suggestions = await get_llm_suggestions(phrase, test_settings, "EN", history=test_history)
        if suggestions is not None:
            print(f"Suggestions (with English detected): {suggestions}")
        else:
            print("Failed to get suggestions.")

if __name__ == "__main__":
    # Configure basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    asyncio.run(main()) 