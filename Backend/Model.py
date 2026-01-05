import cohere
from rich import print
from dotenv import dotenv_values
from cohere.errors import TooManyRequestsError
import time
import re

# Load environment variables
env_vars = dotenv_values('.env')
CohereAPIKey = env_vars.get('CohereAPIKey')

co = cohere.Client(api_key=CohereAPIKey)

funcs = [
    'exit', 'general', 'realtime', 'open', 'close', 'play',
    'generate image', 'system', 'content',
    'google search', 'youtube search', 'reminder'
]

# Rate limiting
last_api_call = 0
MIN_API_INTERVAL = 3  # seconds


def LocalDecisionMaker(prompt: str):
    """
    Fast local pattern matching - NO API CALLS!
    """
    prompt_lower = prompt.lower().strip()

    # EXIT
    if any(word in prompt_lower for word in ['bye', 'goodbye', 'exit', 'quit', 'see you']):
        return ['exit']

    # OPEN
    if re.search(r'\bopen\s+', prompt_lower):
        apps = re.findall(r'\bopen\s+([\w\s]+)', prompt_lower)
        return [f'open {app.strip()}' for app in apps]

    # CLOSE
    if re.search(r'\bclose\s+', prompt_lower):
        apps = re.findall(r'\bclose\s+([\w\s]+)', prompt_lower)
        return [f'close {app.strip()}' for app in apps]

    # PLAY
    if 'play' in prompt_lower and 'display' not in prompt_lower:
        song = prompt_lower.replace('play', '').strip()
        if song:
            return [f'play {song}']

    # GENERATE IMAGE
    if any(p in prompt_lower for p in ['generate image', 'create image', 'make image', 'draw image']):
        img_prompt = re.sub(
            r'(generate|create|make|draw)\s+(an?\s+)?image\s+(of\s+)?',
            '',
            prompt_lower
        ).strip()
        if img_prompt:
            return [f'generate image {img_prompt}']

    # SYSTEM / VOLUME
    if any(word in prompt_lower for word in ['mute', 'unmute', 'volume']):
        level_match = re.search(r'(\d{1,3})', prompt_lower)

        if re.search(r'(set|turn|make|change).{0,10}volume.{0,10}\d', prompt_lower):
            if level_match:
                return [f'system set volume {level_match.group(1)}']

        elif re.search(r'(increase|raise|up|louder).{0,10}volume', prompt_lower):
            amount = level_match.group(1) if level_match else '10'
            return [f'system increase volume {amount}']

        elif re.search(r'(decrease|lower|down|reduce|quieter).{0,10}volume', prompt_lower):
            amount = level_match.group(1) if level_match else '10'
            return [f'system decrease volume {amount}']

        elif 'volume up' in prompt_lower:
            return ['system volume up']
        elif 'volume down' in prompt_lower:
            return ['system volume down']
        elif 'mute' in prompt_lower and 'unmute' not in prompt_lower:
            return ['system mute']
        elif 'unmute' in prompt_lower:
            return ['system unmute']

    # CONTENT
    if any(word in prompt_lower for word in ['write', 'create', 'compose', 'draft']):
        if any(word in prompt_lower for word in [
            'letter', 'email', 'essay', 'application', 'poem',
            'story', 'code', 'script', 'article', 'report',
            'document', 'speech', 'presentation', 'song', 'paragraph'
        ]):
            topic = re.sub(r'(write|create|compose|draft)\s+(a|an|me)?\s*', '', prompt_lower)
            return [f'content {topic.strip()}']

    # REALTIME
    realtime_keywords = [
        'who is', 'what is', 'news', 'weather', 'today',
        'latest', 'current', 'price', 'cost', 'best',
        'top', 'compare', 'review', 'rating'
    ]

    if any(k in prompt_lower for k in realtime_keywords):
        return [f'realtime {prompt}']

    # ✅ YOUTUBE SEARCH (FIXED & PRIORITY)
    if (
        'youtube search' in prompt_lower
        or 'search youtube' in prompt_lower
        or 'search on youtube' in prompt_lower
        or 'on youtube' in prompt_lower
    ):
        topic = re.sub(
            r'(search\s+for\s+|search\s+|youtube\s+search\s+|on\s+youtube)',
            '',
            prompt_lower
        ).strip()
        if topic:
            return [f'youtube search {topic}']

    # GOOGLE SEARCH
    if (
        'google search' in prompt_lower
        or 'search google' in prompt_lower
        or 'search on google' in prompt_lower
        or 'search for' in prompt_lower
    ):
        topic = re.sub(
            r'(google\s+)?search(\s+on)?\s+(google\s+)?(for\s+)?',
            '',
            prompt_lower
        ).strip()
        if topic:
            return [f'google search {topic}']

    # GENERIC SEARCH (LAST)
    if prompt_lower.startswith('search for') or prompt_lower.startswith('search about'):
        topic = re.sub(r'search\s+(for|about)\s+', '', prompt_lower).strip()
        if topic:
            return [f'google search {topic}']

    # TIME / DATE
    if any(word in prompt_lower for word in ['time', 'date', 'day', 'month', 'year']):
        return [f'general {prompt}']

    # DEFAULT
    return [f'general {prompt}']


def APIDecisionMaker(prompt: str):
    """
    Uses Cohere API only for ambiguous general queries
    """
    global last_api_call

    try:
        stream = co.chat_stream(
            model='command-r-plus-08-2024',
            message=prompt,
            temperature=0.7
        )

        response = ""
        for event in stream:
            if event.event_type == 'text-generation':
                response += event.text

        last_api_call = time.time()
        response = response.replace('\n', '').split(',')
        response = [r.strip() for r in response]

        valid = []
        for task in response:
            for f in funcs:
                if task.startswith(f):
                    valid.append(task)

        return valid if valid else None

    except TooManyRequestsError:
        print("⚠️ Rate limit hit, using local logic")
    except Exception as e:
        print(f"⚠️ API Error: {e}")

    return None


def FirstLayerDMM(prompt: str):
    if not prompt or len(prompt.strip()) < 2:
        return ['general hello']

    local = LocalDecisionMaker(prompt)

    priority = [
        'open', 'close', 'play', 'system',
        'generate image', 'content',
        'google search', 'youtube search',
        'exit', 'realtime'
    ]

    if any(local[0].startswith(p) for p in priority):
        return local

    if local[0].startswith('general'):
        if time.time() - last_api_call >= MIN_API_INTERVAL:
            api = APIDecisionMaker(prompt)
            if api:
                return api

    return local


if __name__ == "__main__":
    tests = [
        "search for chaar diwaari on youtube",
        "open chrome",
        "close chrome",
        "turn the volume to 100",
        "decrease the volume by 10",
        "increase the volume by 10",
        "write a letter",
        "generate image of sun",
        "search for pens",
    ]

    for t in tests:
        print(f"\nQuery: {t}")
        print("Decision:", FirstLayerDMM(t))
