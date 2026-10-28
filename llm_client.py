import json
import os

from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env
load_dotenv()

# Read API configuration
api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")

# Create the Groq client
client = Groq(api_key=api_key, timeout=30.0)

def test_groq_connection():
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful B2B sales assistant."
                },
                {
                    "role": "user",
                    "content": "Reply with exactly: Groq API connection successful."
                }
            ],
            temperature=0,
            max_completion_tokens=50
        )

        print("Model:", model)
        print("Response:", response.choices[0].message.content)

    except Exception as error:
        print("Groq API connection failed.")
        print("Error type:", type(error).__name__)
        print("Details:", str(error))

def generate_outreach_batch(leads):
    """Generate personalized messages for multiple leads."""
    
def generate_outreach_batch(leads):
    """Generate personalized messages for multiple leads."""

    if not leads:
        return []

    lead_data = []

    for index, lead in enumerate(leads):
        lead_data.append({
            "lead_id": index,
            "name": str(lead.get("name", "")),
            "company": str(lead.get("company", "")),
            "industry": str(lead.get("industry", "")),
            "score": lead.get("score", 0)
        })

    
    prompt = f"""
You are an expert B2B SaaS sales outreach specialist.

Our product is a workflow automation and analytics platform.

Generate exactly 3 personalized outreach messages for EACH lead.

The three variants must be:
1. Professional email
2. Friendly email
3. Short LinkedIn message

Rules:
- Use the lead's name, company, and industry.
- Explain a relevant potential business benefit.
- Include a clear, natural call to action.
- Do not invent facts about the company.
- Do not claim that we have previously contacted the lead.
- Return valid JSON only.
- Include each lead_id exactly once.

Required JSON format:
{{
    "results": [
        {{
            "lead_id": 0,
            "variants": [
                {{"type": "professional_email", "message": "..."}},
                {{"type": "friendly_email", "message": "..."}},
                {{"type": "linkedin", "message": "..."}}
            ]
        }}
    ]
}}

Lead information:
{json.dumps(lead_data, ensure_ascii=False)}
"""

    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a B2B sales assistant. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
        max_completion_tokens=3000,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    parsed = json.loads(content)

    return parsed["results"]


    return prompt


if __name__ == "__main__":
    test_groq_connection()
