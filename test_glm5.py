import os
import sys
from openai import OpenAI

api_key = "REDACTED_GLM_KEY"
base_url = "https://open.bigmodel.cn/api/coding/paas/v4/"
model = "glm-5"

try:
    print(f"Testing {model} on {base_url}...")
    client = OpenAI(api_key=api_key, base_url=base_url)
    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("Success! Response:", res.choices[0].message.content)
    sys.exit(0)
except Exception as e:
    print(f"Failed: {e}")
