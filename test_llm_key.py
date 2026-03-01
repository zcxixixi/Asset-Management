import os
import sys
from openai import OpenAI

api_key = "REDACTED_API_KEY"
model = "gemini-3-flash"

try:
    print("Testing with default OpenAI Base URL...")
    client = OpenAI(api_key=api_key)
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("Success with OpenAI Base URL!")
    sys.exit(0)
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Testing with Google Gemini OpenAI endpoint...")
    client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("Success with Gemini Base URL!")
    sys.exit(0)
except Exception as e:
    print(f"Failed: {e}")
