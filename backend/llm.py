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

async def get_llm_suggestions(english_text: str) -> list[dict[str, str]] | None:
    """Gets 1-2 simple Italian reply suggestions from GPT-4o mini based on English text, 
       considering the specific user and exam context."""
    if not client:
        logging.error("OpenAI client is not initialized. Cannot get suggestions.")
        return None
    if not english_text or not english_text.strip():
        return [] # Return empty list for empty input

    # Define the persona, context, and task for the LLM
    system_prompt = f"""
You are an assistant helping Clark Ohlenbusch, an intermediate Italian language learner (Italian 102, B1 level), prepare for an oral exam. 
His exam theme is: "Un episodio interessante o divertente del tuo passato."
He needs to use imperfetto and passato prossimo correctly.

Clark's Background:
- Age: 21
- From: Western Massachusetts, lives in Charlestown (Boston)
- Studies: Computer Science
- Heritage: Albanian/French (close to Albanian grandfather)
- Interests: Nature/hiking, languages/cultures, weightlifting, history (Genghis Khan, Sengoku, conflict), travel (Japan)
- Story he will tell: Clark was walking in the woods with his grandfather ("Quando ero piccolo, andavo spesso..."). Grandfather saw a snake, grabbed it, hit it against a tree, and walked on. Clark was surprised and will end by asking the professor "Lei ha mai visto un serpente nella natura?"

Your Task:
Based *only* on the provided English translation of what the *professor* (or the last speaker) just said to Clark, suggest 1 or 2 very simple, common, and relevant Italian replies *that Clark could use*. The replies should be natural for a B1 level student in this exam context, keeping his background in mind where appropriate.

Output Format:
Output ONLY a valid JSON list of objects, where each object has keys 'italian' and 'english'. Even if you only provide one suggestion, it MUST be enclosed in a list. 
Example: [{{"italian": "Sì, una volta l'ho visto.", "english": "Yes, I saw one once."}}, {{"italian": "No, mai!", "english": "No, never!"}}]
"""
    
    # The user_prompt now represents what the *other person* said
    user_prompt = f"What the professor/speaker said to Clark (English translation): \"{english_text}\""

    # Define the model to use *before* the first log message that uses it
    model_name = "gpt-4o-mini" # Reverted back to mini for reliability

    try:
        logging.debug(f"Sending prompt to {model_name} for text: {english_text}")
        response = await client.chat.completions.create(
            model=model_name, # Use the variable defined above
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5, # Lower temperature for more predictable replies
            max_tokens=100,  # Limit response length
            response_format={ "type": "json_object" } # Request JSON output
        )
        
        # Remove the redundant debug log message here
        # logging.debug(f"Sending prompt to {model_name} for text: {english_text}")

        content = response.choices[0].message.content
        logging.debug(f"Received raw response from {model_name}: {content}")

        if content:
            try:
                # Parse the JSON response
                parsed_response = json.loads(content)
                
                suggestions_list = [] # Initialize an empty list

                # Handle if the response is a single dictionary
                if isinstance(parsed_response, dict) and 'italian' in parsed_response and 'english' in parsed_response:
                    logging.debug("LLM returned a single dictionary, wrapping in a list.")
                    suggestions_list = [parsed_response] # Wrap the single dict in a list
                
                # Handle if the response is already a list
                elif isinstance(parsed_response, list) and all(
                    isinstance(item, dict) and 'italian' in item and 'english' in item 
                    for item in parsed_response
                ):
                    suggestions_list = parsed_response # Use the list directly
                
                # Handle unexpected formats
                else:
                    logging.warning(f"LLM response JSON was not the expected list or single dict format: {content}")
                    return [] # Return empty list for unexpected formats
                
                # Limit to max 2 suggestions and return
                return suggestions_list[:2] 

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
    for phrase in test_phrases:
        print(f"\n--- Testing with: '{phrase}' ---")
        suggestions = await get_llm_suggestions(phrase)
        if suggestions is not None:
            print(f"Suggestions: {suggestions}")
        else:
            print("Failed to get suggestions.")

if __name__ == "__main__":
    # Configure basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    asyncio.run(main()) 