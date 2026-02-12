try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from datetime import datetime, timezone, timedelta
from groq import Groq
from json import load, dump
import os
import re
from functools import lru_cache
import threading
from dotenv import dotenv_values

# ===============================
# ENVIRONMENT SETUP
# ===============================
env_vars = dotenv_values('.env')

Username = env_vars.get('Username', 'User')
AssistantName = env_vars.get('AssistantName', 'EcoAI')
GroqAPIKey = env_vars.get('GroqAPIKey')

client = Groq(api_key=GroqAPIKey)

CHATLOG_PATH = 'Data/ChatLog.json'
os.makedirs('Data', exist_ok=True)

if not os.path.exists(CHATLOG_PATH):
    with open(CHATLOG_PATH, 'w') as f:
        dump([], f)

chatlog_lock = threading.Lock()

# ===============================
# OPTIMIZED SYSTEM PROMPTS
# ===============================
BASE_SYSTEM_PROMPT = f"""You are {AssistantName}, a professional AI chatbot.
your features are: answering to general and realtime query, system automation, image generation, write content like letters, creating ppt, taking screenshots and finally recording screen

CRITICAL RULES:
- You are a female assistant
- Answer ONLY the user's query using the provided search data
- Be concise for simple questions (2-4 sentences)
- Be detailed for complex topics (as needed)
- Use natural, conversational language
- For translations: modern versions only, no romanization
- Match the user language. If the user speak to you in hindi then respond in hindi.. if they speaks in spanish, respond in spanish
- NO mentions of search results, just answer directly
- if user asks something about you then respond to them according to their queries
- If user replies in romanized version of a language then reply in original version.. eg: if user speaks to you in hinglish then talk to them in Hindi
- If user ask who creatd yopu then you have to say that Vaibhav have created you professionally and patiently
- If User's query is about then you have to be a professional coder and think rationally about everything
- IMPORTANT FOR SPEECH: NEVER use numbered lists (1., 2., 3.), bullet points (-, *, •), or markdown **bold**, *italic*, __underline__. Write in smooth, flowing sentences only. No formatting symbols at all."""

# ENVIRONMENT_SYSTEM_PROMPT = """ENVIRONMENT/SUSTAINABILITY QUERY

# Response requirements:
# - Detailed scientific explanation (10-12 lines)
# - Include causes, effects, and impacts
# - Use professional scientific language
# - Real-world relevance and examples
# - Suitable for science exhibition
# - NO emojis or casual tone
# - Write in flowing paragraphs — no numbered or bulleted lists, no **bold** or markdown."""

# ===============================
# CACHED REALTIME INFO
# ===============================
_info_cache = None
_info_cache_time = 0

def Information():
    global _info_cache, _info_cache_time
    
    current = datetime.now().timestamp()
    
    if _info_cache and (current - _info_cache_time) < 60:
        return _info_cache
    
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    
    _info_cache = (
        f"Date: {ist_now.strftime('%d %B %Y')}\n"
        f"Day: {ist_now.strftime('%A')}\n"
        f"Time: {ist_now.strftime('%H:%M:%S')} IST\n"
    )
    _info_cache_time = current
    
    return _info_cache

# ===============================
# OPTIMIZED SEARCH WITH THREADING
# ===============================
_search_cache = {}
_search_cache_lock = threading.Lock()
SEARCH_CACHE_DURATION = 300  # 5 minutes

@lru_cache(maxsize=128)
def normalize_search_query(query):
    return ' '.join(query.lower().strip().split())

def GoogleSearch(query, max_results=5):
    normalized = normalize_search_query(query)
    
    with _search_cache_lock:
        if normalized in _search_cache:
            cache_time, cached_data = _search_cache[normalized]
            if datetime.now().timestamp() - cache_time < SEARCH_CACHE_DURATION:
                print("💾 Using cached search results")
                return cached_data
    
    text_data = ""
    sources = []
    
    try:
        with DDGS(timeout=10) as ddgs:
            results = ddgs.text(query, max_results=max_results)
            for r in results:
                if r.get("href"):
                    sources.append(r["href"])
                if r.get("body"):
                    text_data += r["body"] + "\n"
        
        if len(text_data) > 2000:
            text_data = text_data[:2000] + "..."
    
    except Exception as e:
        print(f"Search error: {e}")
    
    if not sources:
        sources = [
            "https://www.un.org/en/climatechange",
            "https://www.ipcc.ch",
            "https://www.worldbank.org/en/topic/environment"
        ]
    
    result = (text_data.strip(), sources)
    
    with _search_cache_lock:
        _search_cache[normalized] = (datetime.now().timestamp(), result)
        if len(_search_cache) > 50:
            oldest_key = min(_search_cache.keys(), key=lambda k: _search_cache[k][0])
            del _search_cache[oldest_key]
    
    return result

# ===============================
# QUERY CLASSIFICATION (CACHED)
# ===============================
@lru_cache(maxsize=256)
# def is_environment_query(query):
#     keywords = [
#         "environment", "climate", "global warming", "pollution",
#         "sustainability", "renewable", "ecosystem", "biodiversity",
#         "carbon", "greenhouse", "solar", "wind", "plastic",
#         "deforestation", "wildlife", "conservation", "nature",
#         "ecology", "emissions", "fossil", "ozone", "recycle"
#     ]
#     return any(k in query.lower() for k in keywords)

# ===============================
# CHATLOG MANAGEMENT (OPTIMIZED)
# ===============================
def load_chatlog():
    with chatlog_lock:
        try:
            with open(CHATLOG_PATH, 'r') as f:
                messages = load(f)
            if len(messages) > 15:
                messages = messages[-15:]
            return messages
        except:
            return []

def save_chatlog(messages):
    with chatlog_lock:
        try:
            if len(messages) > 15:
                messages = messages[-15:]
            with open(CHATLOG_PATH, 'w') as f:
                dump(messages, f, indent=2)
        except Exception as e:
            print(f"Error saving chatlog: {e}")

# ===============================
# RESPONSE CLEANING
# ===============================
def clean_response(text: str) -> str:
    text = re.sub(r"</s>", "", text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ===============================
# MAIN REALTIME SEARCH ENGINE (OPTIMIZED)
# ===============================
def RealtimeSearchEngine(prompt, use_streaming=True):
    try:
        messages = load_chatlog()
        # env_query = is_environment_query(prompt)
        
        search_thread = threading.Thread(
            target=lambda: GoogleSearch(prompt, max_results=5)
        )
        search_thread.start()
        search_thread.join(timeout=8)
        
        realtime_text, source_links = GoogleSearch(prompt, max_results=5)
        
        system_msgs = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "system", "content": Information()}
        ]
        
        if realtime_text:
            system_msgs.append({
                "role": "system",
                "content": f"Search Results:\n{realtime_text[:1500]}"
            })
        
        # if env_query:
        #     system_msgs.insert(1, {"role": "system", "content": BASE_SYSTEM_PROMPT})
        
        messages.append({"role": "user", "content": prompt})
        
        # # max_tokens = 2048 if env_query else 512
        # # temperature = 0.5 if env_query else 0.3
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=system_msgs + messages,
            temperature=0.7,
            max_tokens=8192,
            stream=use_streaming,
            top_p=0.9
        )
        
        answer = ""
        if use_streaming:
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    answer += chunk.choices[0].delta.content
        else:
            answer = completion.choices[0].message.content
        
        answer = clean_response(answer)
        
        messages.append({"role": "assistant", "content": answer})
        save_chatlog(messages)
        
        return answer
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "rate" in error_msg or "limit" in error_msg:
            print("⚠️ Rate limit, clearing history...")
            save_chatlog([])
            try:
                system_msgs = [
                    {"role": "system", "content": BASE_SYSTEM_PROMPT},
                    {"role": "system", "content": Information()}
                ]
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=system_msgs + [{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=512,
                    stream=False
                )
                return clean_response(completion.choices[0].message.content)
            except:
                return "I'm experiencing high load. Please try again in a moment."
        
        elif "context" in error_msg or "token" in error_msg:
            print("⚠️ Context too long, clearing...")
            save_chatlog([])
            return RealtimeSearchEngine(prompt, use_streaming=False)
        
        else:
            print(f"Fatal Error: {e}")
            return "I encountered an error processing your request. Please try rephrasing."

# ===============================
# UTILITY FUNCTIONS
# ===============================
def clear_search_cache():
    with _search_cache_lock:
        _search_cache.clear()
    print("🧹 Search cache cleared")

def get_cache_stats():
    with _search_cache_lock:
        return {
            'search_cache_size': len(_search_cache),
            'cached_queries': list(_search_cache.keys())
        }

if __name__ == "__main__":
    import time
    
    print(f"{'='*60}")
    print(f"  {AssistantName} Realtime Search Engine (Enhanced)")
    print(f"{'='*60}\n")
    
    test_queries = [
        "who is the current president of USA",
        "what is climate change",
        "latest news about AI",
        "weather today",
        "who are you",
        "what are your features"
    ]
    
    print("Running performance tests...\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        start = time.time()
        response = RealtimeSearchEngine(query)
        elapsed = time.time() - start
        print(f"Response: {response[:100]}...")
        print(f"Time: {elapsed:.2f}s\n")
    
    print(f"Cache Stats: {get_cache_stats()}\n")
    
    print("Interactive mode (type 'exit' to quit):\n")
    while True:
        q = input(">>> ").strip()
        if q.lower() == 'exit':
            break
        if q.lower() == 'clear':
            clear_search_cache()
            save_chatlog([])
            continue
        if q:
            print(RealtimeSearchEngine(q))
<<<<<<< HEAD
            print()
=======
            print()
>>>>>>> 3f7e11d900acadde38fd561f6d620bf0b777ade8
