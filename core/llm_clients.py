from core.config import settings

# Initialize OpenAI
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception as e:
    openai_client = None
    print(f"Warning: Failed to initialize OpenAI client - {e}")

# Initialize Gemini
try:
    from google import genai
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    gemini_client = None
    print(f"Warning: Failed to initialize Gemini client - {e}")

# Initialize Anthropic
try:
    import anthropic
    anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
except Exception as e:
    anthropic_client = None
    print(f"Warning: Failed to initialize Anthropic client - {e}")
