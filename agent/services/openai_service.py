import os
from typing import Any

import openai


class OpenAIService:
    def __init__(self, settings):
        self.settings = settings
        self.client = openai.OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.embedding_model = self.settings.embedding_model

    def create_completion(self, prompt: str, max_tokens: int = 700) -> str:
        # Mock response for testing
        if os.getenv("OPENAI_MOCK", "").lower() == "true":
            return """
### Change Summary
Added a new feature function to the example.py file.

### What Changed
- Added `new_feature()` function that prints a message.

### Why Change Was Made
To demonstrate adding new functionality.

### Impact Analysis
Low impact, adds new code without modifying existing logic.

### Risk Assessment
Minimal risk, no breaking changes.

### Recommendation
Build new code as it's a simple addition.

### Developer Summary
A straightforward feature addition with clear intent.
""".strip()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an AI Engineering Agent helping developers understand code changes."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        if os.getenv("OPENAI_MOCK", "").lower() == "true":
            # Mock embeddings
            import random
            return [[random.random() for _ in range(1536)] for _ in texts]
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def summarize_diff(self, diff_text: str, context: str) -> str:
        prompt = (
            "Analyze the following git diff and produce a structured report in markdown. "
            "Please return concise sections: Change Summary, What Changed, Why Change Was Made, "
            "Impact Analysis, Risk Assessment, Recommendation, Developer Summary.\n\n"
            f"Context: {context}\n\n"
            f"Diff:\n{diff_text}\n"
        )
        return self.create_completion(prompt)
