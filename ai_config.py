# ai_config.py - Multi-provider AI configuration (API-key Gemini)
import os
from dotenv import load_dotenv

load_dotenv(".env-local")

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")


def get_ai_client():
    """Return AI client based on provider"""

    if AI_PROVIDER == "openai":
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        return openai

    elif AI_PROVIDER == "anthropic":
        from anthropic import Anthropic
        return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    elif AI_PROVIDER == "gemini":
        # API-key Gemini (google-generativeai 0.8.6)
        import google.genai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=api_key)
        return genai

    elif AI_PROVIDER == "ollama":
        import requests

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        class OllamaClient:
            def __init__(self, base_url):
                self.base_url = base_url

            def generate(self, prompt, model):
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model, "prompt": prompt},
                    timeout=60
                )
                response.raise_for_status()
                return response.json()

        return OllamaClient(base_url)

    else:
        raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")


def generate_completion(prompt, system_prompt="", max_tokens=4000):
    """Generate AI completion"""
    client = get_ai_client()

    if AI_PROVIDER == "openai":
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    elif AI_PROVIDER == "anthropic":
        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    elif AI_PROVIDER == "gemini":
        model = client.GenerativeModel(AI_MODEL)

        full_prompt = (
            f"{system_prompt}\n\n{prompt}"
            if system_prompt else prompt
        )

        response = model.generate_content(
            full_prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.2,
            }
        )

        return response.text

    elif AI_PROVIDER == "ollama":
        full_prompt = f"{system_prompt}\n\n{prompt}"
        response = client.generate(full_prompt, AI_MODEL)
        return response.get("response", "")


# ============================================================================
# SELF TEST
# ============================================================================

if __name__ == "__main__":
    print("🔧 AI Configuration Test")
    print("=" * 50)
    print(f"Provider: {AI_PROVIDER}")
    print(f"Model: {AI_MODEL}")
    print("=" * 50)

    try:
        response = generate_completion(
            prompt="Reply with: Gemini connection successful",
            system_prompt="You are a test assistant.",
            max_tokens=50
        )

        print("\n✅ GEMINI connection successful!")
        print(f"   Model: {AI_MODEL}")
        print(f"   Test response: {response}")

    except Exception as e:
        print("\n❌ AI connection failed")
        print(f"   Error: {e}")
