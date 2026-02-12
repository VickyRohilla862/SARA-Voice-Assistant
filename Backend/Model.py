import cohere
from rich import print
from dotenv import dotenv_values
from cohere.errors import TooManyRequestsError
import time
import re
from functools import lru_cache
import threading
from groq import Groq
import json

# Load environment variables
env_vars = dotenv_values('.env')
CohereAPIKey = env_vars.get('CohereAPIKey')
GroqAPIKey = env_vars.get('GroqAPIKey')

co = cohere.Client(api_key=CohereAPIKey) if CohereAPIKey else None
groq_client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None

if not groq_client:
    print("⚠️ No Groq API key found; skipping preprocessing")
if not co:
    print("⚠️ No Cohere API key found; skipping API fallback")

funcs = [
    'exit', 'general', 'realtime', 'open', 'close', 'play',
    'generate image', 'system', 'content', 'content presentation',
    'google search', 'youtube search', 'run', 'reminder', 'generate image'
]

# RATE LIMITING WITH CACHE
last_api_call = 0
MIN_API_INTERVAL = 0.8
api_cache = {}
cache_lock = threading.Lock()
MAX_CACHE_SIZE = 200

@lru_cache(maxsize=512)
def normalize_query(query):
    return ' '.join(query.lower().strip().split())

# PREPROCESS QUERY WITH GROQ (skipped for short/simple queries)
def preprocess_query(raw_prompt: str):
    if not groq_client:
        return None
    if len(raw_prompt.split()) < 10:
        return None
    try:
        system_prompt = """
        You are a query preprocessor. Tasks:
        1. Correct spelling mistakes.
        2. Split into individual commands based on actions (verbs like open, close, turn, create, search).
        3. Infer splits even without 'and'/ 'then'.
        4. Output ONLY a JSON array: ["corrected cmd1", "corrected cmd2"]
        Example input: "open chorme opn edg turn volme to 100"
        Output: ["open chrome", "open edge", "turn volume to 100"]
        If there is only one command then the output will be ["command"]
        No other text.
        """
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_prompt}
            ],
            temperature=0.3,
            max_tokens=200,
        )
        response = completion.choices[0].message.content.strip()
        try:
            commands = json.loads(response)
            if isinstance(commands, list) and all(isinstance(c, str) for c in commands):
                return commands
        except json.JSONDecodeError:
            pass
    except Exception as e:
        print(f"⚠️ Groq preprocess error: {e}")
    return None

# SMART MULTI-COMMAND SPLITTER
def split_multi_commands(prompt: str):
    prompt = prompt.strip().replace('\n', ' ')
    prompt_lower = prompt.lower()
    action_verbs = [
        'open', 'close', 'play', 'search', 'create', 'make',
        'write', 'generate image', 'generate', 'set', 'increase', 'decrease',
        'mute', 'unmute', 'run', 'execute', 'start', 'stop', 'turn',
        'take', 'record'
    ]
    
    conjunction_parts = re.split(r'\s+(and|then)\s+', prompt, flags=re.IGNORECASE)
    commands = []
    
    for conj_part in conjunction_parts:
        if conj_part and conj_part.lower() in ['and', 'then']:
            continue
        words = conj_part.split()
        current_cmd = []
        for word in words:
            if word.lower() in action_verbs and current_cmd:
                commands.append(' '.join(current_cmd).strip())
                current_cmd = [word]
            else:
                current_cmd.append(word)
        if current_cmd:
            commands.append(' '.join(current_cmd).strip())
            
    final_commands = []
    last_action = None
    for cmd in commands:
        if not cmd: continue
        first_word = cmd.split()[0].lower() if cmd.split() else ''
        if first_word in action_verbs:
            last_action = first_word if first_word in ['open', 'close'] else None
            final_commands.append(cmd)
        elif last_action:
            final_commands.append(f"{last_action} {cmd}")
        else:
            final_commands.append(cmd)
            
    return final_commands if len(final_commands) > 1 else [prompt]

# ────────────────────────────────────────────────
# HELPER: better extraction for search & play
# ────────────────────────────────────────────────
def extract_query_and_platform(text: str, default_platform: str = None) -> tuple[str, str]:
    text_lower = text.lower().strip()
    
    platform_markers = {
        "on google": "google",
        "in google": "google",
        "google": "google",
        "on youtube": "youtube",
        "in youtube": "youtube",
        "youtube": "youtube",
        "on yt": "youtube",
        "yt": "youtube"
    }
    
    detected_platform = None
    clean_text = text_lower
    
    for marker in sorted(platform_markers, key=len, reverse=True):
        if marker in clean_text:
            clean_text = clean_text.replace(marker, "").strip()
            detected_platform = platform_markers[marker]
            break
    
    prefixes = [
        "search for", "search", "find", "look for",
        "google search", "youtube search",
        "play on", "play"
    ]
    for prefix in sorted(prefixes, key=len, reverse=True):
        if clean_text.startswith(prefix):
            clean_text = clean_text[len(prefix):].strip()
            break
    
    if default_platform and not detected_platform:
        detected_platform = default_platform
    
    clean_query = clean_text.strip().rstrip("?.!,")
    
    return clean_query, detected_platform

# ────────────────────────────────────────────────
# LOCAL DECISION MAKER (FAST RULES) ── IMPROVED VERSION
# ────────────────────────────────────────────────
def LocalDecisionMaker(prompt: str):
    if not prompt or not prompt.strip():
        return ['general hello']
    
    prompt_lower = prompt.lower().strip()
    
    # EXIT
    if prompt_lower in ['exit', 'quit', 'bye', 'goodbye', 'stop']:
        return ['exit']
    
    # SYSTEM COMMANDS
    system_patterns = [
        r'set\s+volume\s+to', r'turn\s+(the\s+)?volume\s+to',
        r'(increase|decrease|raise|lower)\s+volume',
        r'mute(\s+volume|\s+sound|\s+the\s+volume)?',
        r'unmute(\s+volume|\s+sound|\s+the\s+volume)?',
        r'take\s+(a\s+)?screenshot',
        r'screenshot',
        r'(start|begin)\s+(screen\s+)?recording',
        r'(record|recording)\s+screen'
    ]
    for pattern in system_patterns:
        if re.search(pattern, prompt_lower, re.I):
            if 'screenshot' in prompt_lower:
                return ['system screenshot']
            if any(w in prompt_lower for w in ['record', 'recording']):
                return ['system start screen recording']
            if any(w in prompt_lower for w in ['mute', 'unmute']):
                return [f'system {prompt_lower}']
            if 'volume' in prompt_lower:
                level_match = re.search(r'(to|set to|at)\s*(\d+)', prompt_lower, re.I)
                if level_match:
                    return [f'system set to {level_match.group(2)}']
                return [f'system {prompt_lower}']

    # OPEN / CLOSE ── clean version without duplication
    if prompt_lower.startswith(('open ', 'launch ', 'start ')):
        app = re.sub(r'^(open|launch|start)\s+', '', prompt_lower, flags=re.I).strip(' .')
        return [f'open {app}']
    
    if prompt_lower.startswith(('close ', 'kill ', 'exit ')):
        app = re.sub(r'^(close|kill|exit)\s+', '', prompt_lower, flags=re.I).strip(' .')
        return [f'close {app}']
    
    # ══════════════════════════════════════════════════════════════
    # CONTENT / PPT / SONG / LETTER / ESSAY ── FIXED VERSION
    # ══════════════════════════════════════════════════════════════
    content_starters = ['write', 'create', 'make', 'draft', 'prepare', 'compose']
    if any(prompt_lower.startswith(s + ' ') for s in content_starters):
        
        # Step 1: Remove the starter verb
        remaining = prompt_lower
        for starter in content_starters:
            if remaining.startswith(starter + ' '):
                remaining = remaining[len(starter):].strip()
                break
        
        # Step 2: Remove optional articles (a, an, the)
        if remaining.startswith(('a ', 'an ', 'the ')):
            remaining = re.sub(r'^(a|an|the)\s+', '', remaining, flags=re.I).strip()
        
        # Step 3: Check for presentation first (highest priority)
        ppt_markers = ['ppt', 'powerpoint', 'presentation', 'slide show', 'slides']
        if any(marker in remaining for marker in ppt_markers):
            # Remove PPT markers and extract topic
            topic = remaining
            for marker in ppt_markers:
                topic = topic.replace(marker, '')
            # Remove connector words
            topic = re.sub(r'\b(on|about|for|regarding|of)\b', '', topic, flags=re.I)
            topic = re.sub(r'\s+', ' ', topic).strip()
            if not topic:
                topic = "Untitled"
            return [f'content presentation {topic}']
        
        # Step 4: Detect content type (song, letter, essay, etc.)
        content_types = ['song', 'letter', 'poem', 'story', 'email', 'message', 
                        'note', 'essay', 'article', 'report', 'document', 'paper']
        
        detected_type = None
        topic_text = remaining
        
        # Check if first word is a content type
        first_word = remaining.split()[0] if remaining.split() else ''
        if first_word in content_types:
            detected_type = first_word
            # Remove the content type from remaining text
            topic_text = remaining[len(first_word):].strip()
        else:
            # Default to generic content
            detected_type = "document"
            topic_text = remaining
        
        # Step 5: Clean up topic text - remove connector words
        topic_text = re.sub(r'^\b(on|about|for|regarding|of|to)\b\s*', '', topic_text, flags=re.I)
        topic_text = re.sub(r'\s+', ' ', topic_text).strip()
        
        # Step 6: If no topic, use default
        if not topic_text or len(topic_text) < 2:
            topic_text = "Untitled"
        
        # Return proper format
        return [f'content {detected_type} {topic_text}']
    
    # ══════════════════════════════════════════════════════════════
    # GENERATE IMAGE ── HIGH PRIORITY
    # ══════════════════════════════════════════════════════════════
    if re.match(r'^(generate|create|make|draw)\s+(an?\s+)?(image|picture|photo|art|drawing)\b', prompt_lower):
        img_prompt = re.sub(
            r'^(generate|create|make|draw)\s+(an?\s+)?(image|picture|photo|art|drawing)\s*(of|for|about)?\s*',
            '',
            prompt_lower,
            flags=re.I
        ).strip(' .')

        if not img_prompt:
            img_prompt = "Untitled"

        return [f'generate image {img_prompt}']

    
    
    # RUN COMMAND
    if re.search(r'\brun\s+', prompt_lower):
        cmd = re.sub(r'\brun\s+', '', prompt_lower).strip().rstrip('.,!?')
        if cmd:
            return [f'run {cmd}']
    
    # REMINDER stub
    if 'remind' in prompt_lower or 'reminder' in prompt_lower:
        return [f'reminder {prompt}']
    
    # REALTIME / GENERAL
    realtime_keywords = [
        'weather', 'news', 'latest', 'current', 'update on',
        'stock', 'price', 'currency', 'crypto', 'bitcoin',
        'time', 'date', 'day', 'month', 'year', 'clock'
    ]
    question_starters = ['who', 'what', 'where', 'when', 'why', 'how']
    if any(prompt_lower.startswith(q + ' ') for q in question_starters) or any(k in prompt_lower for k in realtime_keywords):
        return [f'realtime {prompt}']
    
    # GOOGLE / YOUTUBE SEARCH ── preserved original good logic
    search_indicators = ["search for", "search", "google search", "find", "look for"]
    if any(ind in prompt_lower for ind in search_indicators):
        query_part, platform = extract_query_and_platform(prompt, default_platform="google")
        if platform == "youtube":
            return [f'youtube search {query_part}']
        else:
            return [f'google search {query_part}']
    
    # PLAY ── preserved original good logic
    if prompt_lower.startswith("play ") or "play" in prompt_lower.split()[:3]:
        query_part, _ = extract_query_and_platform(prompt)
        return [f'play {query_part}']

    # TIME / DATE fast path
    time_keywords = ['time', 'date', 'day', 'month', 'year', 'clock', "what's the time"]
    if any(word in prompt_lower for word in time_keywords):
        return [f'general {prompt}']
    
    # DEFAULT
    return [f'general {prompt}']

# API DECISION MAKER (fallback only)
def APIDecisionMaker(prompt: str):
    global last_api_call
    normalized = normalize_query(prompt)
    with cache_lock:
        if normalized in api_cache:
            print("💾 Using cached result")
            return api_cache[normalized]
            
    time_since_last = time.time() - last_api_call
    if time_since_last < MIN_API_INTERVAL:
        time.sleep(MIN_API_INTERVAL - time_since_last)
        
    try:
        response = co.chat(
            model='command-r-plus-08-2024',
            message=f"Classify this query into one of these actions: {', '.join(funcs)}. Query: {prompt}",
            temperature=0.1,
            max_tokens=30,
        )
        last_api_call = time.time()
        text = response.text.lower().strip()
        tasks = []
        for func in funcs:
            if func in text:
                if func in ['open', 'close', 'play', 'google search', 'youtube search']:
                    remaining = prompt.lower().replace(func, '').strip()
                    tasks.append(f'{func} {remaining}' if remaining else func)
                else:
                    tasks.append(f'{func} {prompt}')
                break
        result = tasks if tasks else None
        with cache_lock:
            if len(api_cache) >= MAX_CACHE_SIZE:
                api_cache.pop(next(iter(api_cache)))
            api_cache[normalized] = result
        return result
    except Exception as e:
        print(f"⚠️ API Error: {e}")
    return None

# FIRST LAYER DECISION MAKER
# In Model.py -> Find FirstLayerDMM function

def FirstLayerDMM(prompt: str):
    if not prompt or len(prompt.strip()) < 2:
        return ['general hello']
    
    preprocessed = preprocess_query(prompt)
    if preprocessed:
        commands = preprocessed
    else:
        # REMOVED: The 'if re.search' guard that required 'and'/'then'
        # Now it will always try to split based on action verbs (open, close, etc.)
        commands = split_multi_commands(prompt)

    all_tasks = []
    for cmd in commands:
        local_result = LocalDecisionMaker(cmd)
        all_tasks.extend(local_result)
        
    # If any task in the list is NOT general, trust the sequence
    if all_tasks and not any(t.startswith("general") for t in all_tasks):
        return all_tasks

    # Only fallback if the whole thing is just one 'general' task
    if len(all_tasks) == 1 and all_tasks[0].startswith("general"):
        if time.time() - last_api_call >= MIN_API_INTERVAL:
            api_result = APIDecisionMaker(prompt)
            if api_result:
                return api_result

    return all_tasks

# UTILITY
def clear_cache():
    with cache_lock:
        api_cache.clear()
    print("🧹 Cache cleared")

if __name__ == "__main__":
    tests = [
        "write an essay on ai",
        "write a song about rain",
        "create a ppt on ai",
        "Generate image of AI",
        "make presentation on climate change",
        "write a song",
        "write letter to principal",
        "write a letter for my friend",
        "create essay on technology",
        "make a report about climate change",
        "write article on sports",
        "play despacito",
        "open chrome",
        "close edge",
        "take screenshot",
        "start screen recording",
        "mute volume",
        "set volume to 70",
    ]
    
    print("=" * 70)
    print("MODEL.PY - DECISION MAKING TEST")
    print("=" * 70)
    print()
    
    for t in tests:
        result = FirstLayerDMM(input(">>> "))
        status = "✅" if "content content" not in str(result) and "n essay" not in str(result) else "❌"
        print(f"{status} Query: '{t}'")
        print(f"   Decision: {result}")
<<<<<<< HEAD
        print()
=======
        print()
>>>>>>> 3f7e11d900acadde38fd561f6d620bf0b777ade8
