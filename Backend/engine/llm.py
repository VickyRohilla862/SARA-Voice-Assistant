<<<<<<< HEAD
import os, json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GroqAPIKey"))

SYSTEM_PROMPT = """
You are an intent classifier for a Windows automation assistant.

Return ONLY valid JSON.

Schema:
{
  "intent": "<intent>",
  "args": { }
}

Supported intents:
- open_app (name)
- close_app (name)
- set_volume (level)
- mute_volume
- unmute_volume
- create_presentation (topic)
- write_letter (reason)
- capabilities
"""

def parse_intent(user_input: str):
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0
    )

    return json.loads(r.choices[0].message.content)
=======
import os, json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GroqAPIKey"))

SYSTEM_PROMPT = """
You are an intent classifier for a Windows automation assistant.

Return ONLY valid JSON.

Schema:
{
  "intent": "<intent>",
  "args": { }
}

Supported intents:
- open_app (name)
- close_app (name)
- set_volume (level)
- mute_volume
- unmute_volume
- create_presentation (topic)
- write_letter (reason)
- capabilities
"""

def parse_intent(user_input: str):
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0
    )

    return json.loads(r.choices[0].message.content)
>>>>>>> 3f7e11d900acadde38fd561f6d620bf0b777ade8
