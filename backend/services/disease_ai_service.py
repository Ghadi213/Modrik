from dotenv import load_dotenv
import os
import requests

load_dotenv()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)


def ask_ai(prompt: str) -> str:

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

            "Content-Type":
                "application/json",
        },

        json={
            "model":
                "openai/gpt-4o-mini",

            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        },
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]


def translate_disease_name(
    disease_name: str
) -> str:

    prompt = f"""
Find the correct Arabic medical name for this disease using the terminology commonly used in trusted Arabic medical sources such as:

- Mayo Clinic Arabic
- Cleveland Clinic Abu Dhabi Arabic
- MSD Manuals Arabic
- Arabic medical references and hospitals

Rules:
- Use the medically recognized Arabic disease name.
- Use the same wording style used in trusted Arabic medical websites.
- Do not translate word by word.
- Do not explain the disease.
- Do not describe the disease.
- Do not invent Arabic names.
- Return only the disease name in Arabic.

Disease:
{disease_name}
"""

    return ask_ai(prompt).strip()


def explain_disease_name(
    disease_name: str,
    language: str
) -> str:

    if language == "ar":

        language_instruction = """
Respond ONLY in Arabic.
Use natural Arabic.
Use simple language suitable for normal users.
"""

    else:

        language_instruction = """
Respond ONLY in English.
Use simple natural English.
"""

    prompt = f"""
Explain this disease in a friendly and simple way for a normal user.

Rules:
- Explain what the disease generally affects.
- Use very simple language.
- Make the explanation sound natural and human.
- Keep it short (5-7 lines).
- Do not diagnose.
- Do not mention treatments.
- Avoid complicated medical terms.
- Do not repeat the disease name in the response.
- The explanation is medical. Use medical meanings for words.

{language_instruction}

Disease:
{disease_name}
"""

    return ask_ai(prompt).strip()