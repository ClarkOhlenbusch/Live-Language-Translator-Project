import deepl
import os
import logging
from dotenv import load_dotenv
import asyncio

load_dotenv() # Load environment variables from .env file

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
if not DEEPL_API_KEY:
    logging.warning("No DEEPL_API_KEY found in .env file. Translation will likely fail.")

# Initialize the DeepL translator client
# Note: Free API keys might have different authentication or endpoint needs.
# Check DeepL Python library documentation if issues arise with Free plan.
translator = None
if DEEPL_API_KEY:
    try:
        # Determine if it's a Free or Pro key based on the suffix ':fx'
        server_url = None # Default to Pro endpoint
        if DEEPL_API_KEY.endswith(":fx"):
             server_url = "https://api-free.deepl.com" 
             logging.info("Using DeepL Free API endpoint.")
        else:
             logging.info("Using DeepL Pro API endpoint.")
             
        auth_key = DEEPL_API_KEY # Use the full key for authentication
        translator = deepl.Translator(auth_key, server_url=server_url)
        # Verify connection by checking usage (optional, might consume quota)
        # usage = translator.get_usage()
        # logging.info(f"DeepL API usage: {usage.character}")
        logging.info("DeepL Translator initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize DeepL translator: {e}", exc_info=True)
        translator = None # Ensure translator is None if init fails
else:
    logging.warning("DeepL API key not provided. Translator cannot be initialized.")

async def translate_text(text: str, target_lang="EN-US") -> str | None:
    """Translates Italian text to the target language using DeepL."""
    if not translator:
        logging.error("DeepL translator is not initialized. Cannot translate.")
        return None
    if not text or not text.strip():
        # Don't waste API calls on empty strings
        return ""
        
    try:
        # Source language is explicitly set to Italian ("IT")
        result = translator.translate_text(text, source_lang="IT", target_lang=target_lang)
        # logging.debug(f"Translated '{text}' -> '{result.text}'")
        return result.text
    except deepl.DeepLException as e:
        logging.error(f"DeepL API error during translation: {e}")
        return None
    except Exception as e:
        # Catch other potential errors (network issues, etc.)
        logging.error(f"Unexpected error during translation: {e}", exc_info=True)
        return None

# Example usage (for testing this module directly)
async def main():
    italian_phrases = [
        "Ciao come stai?",
        "Questo è un test.",
        "Per favore, traducimi."
    ]
    for phrase in italian_phrases:
        translation = await translate_text(phrase)
        if translation:
            print(f"'{phrase}' -> '{translation}'")
        else:
            print(f"Failed to translate '{phrase}'")

if __name__ == "__main__":
    asyncio.run(main()) 