from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os
import re
import threading
from functools import lru_cache

# ===============================
# ENVIRONMENT SETUP
# ===============================
env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
AssistantName = env_vars.get("AssistantName", "EcoAI")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

CHATLOG_PATH = "Data/ChatLog.json"
chatlog_lock = threading.Lock()

# ===============================
# OPTIMIZED SYSTEM PROMPTS
# ===============================
BASE_SYSTEM_PROMPT = f"""You are {AssistantName}, a professional AI assistant.
your features are: answering to general and realtime query, system automation, image generation, write content like letters, creating ppt, taking screenshots and finally recording screen

Rules:
- You are a female assistant
- Answer ONLY the user's query with precision
- Be concise for simple questions (1-3 sentences)
- Be detailed for complex topics (as needed)
- Use natural, conversational language
- For translations: use modern versions, no romanization
- Match the user language. If the user speak to you in hindi then respond in hindi.. if they speaks in spanish, respond in spanish
- No mentions of training data, APIs, or limitations
- if user asks something about you then respond to them according to their queries
- If user replies in romanized version of a language then reply in original version.. eg: if user speaks to you in hinglish then talk to them in Hindi
- If user ask who creatd yopu then you have to say that Vaibhav have created you professionally and patiently
- IMPORTANT FOR SPEECH OUTPUT: NEVER use numbered lists (1., 2., 3.), bullet points (-, *, •), or markdown **bold**, *italic*, __underline__. Always write in smooth, flowing natural sentences or short paragraphs. No formatting symbols at all.
- If User's query is about then you have to be a professional coder and think rationally about everything
"""

# ENVIRONMENT_SYSTEM_PROMPT = """ENVIRONMENT/SUSTAINABILITY QUERY DETECTED

# Response format:
# - Detailed scientific explanation (8-12 lines)
# - Clear causes and effects
# - Real-world impact and relevance
# - Professional scientific language
# - Suitable for science exhibition
# - NO emojis or casual language
# - Write in flowing paragraphs — no numbered or bulleted lists, no **bold** or markdown."""

# ===============================
# ENHANCED CHAT LOG MANAGEMENT
# ===============================
if not os.path.exists("Data"):
    os.makedirs("Data")

if not os.path.exists(CHATLOG_PATH):
    with open(CHATLOG_PATH, "w") as f:
        dump([], f)

def load_chatlog():
    with chatlog_lock:
        try:
            with open(CHATLOG_PATH, "r") as f:
                messages = load(f)
            if len(messages) > 20:
                messages = messages[-20:]
                with open(CHATLOG_PATH, "w") as f:
                    dump(messages, f, indent=2)
            return messages
        except Exception as e:
            print(f"Error loading chatlog: {e}")
            return []

def save_chatlog(messages):
    with chatlog_lock:
        try:
            if len(messages) > 20:
                messages = messages[-20:]
            with open(CHATLOG_PATH, "w") as f:
                dump(messages, f, indent=2)
        except Exception as e:
            print(f"Error saving chatlog: {e}")

# ===============================
# REALTIME INFO (CACHED)
# ===============================
_info_cache = None
_info_cache_time = 0
INFO_CACHE_DURATION = 60

def RealtimeInformation():
    global _info_cache, _info_cache_time
    current_time = datetime.datetime.now().timestamp()
    
    if _info_cache and (current_time - _info_cache_time) < INFO_CACHE_DURATION:
        return _info_cache
    
    now = datetime.datetime.now()
    _info_cache = (
        f"Date: {now.strftime('%d %B %Y')}\n"
        f"Day: {now.strftime('%A')}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
    )
    _info_cache_time = current_time
    return _info_cache

# ===============================
# QUERY CLASSIFICATION (OPTIMIZED)
# ===============================
@lru_cache(maxsize=256)
# def is_environment_query(query: str) -> bool:
#     keywords = [
#         "environment", "climate", "global warming", "pollution",
#         "sustainability", "renewable", "ecosystem", "biodiversity",
#         "carbon", "greenhouse", "solar", "wind energy", "plastic",
#         "deforestation", "wildlife", "conservation", "nature",
#         "ecology", "emissions", "fossil fuel", "ozone", "recycle"
#     ]
#     query_lower = query.lower()
#     return any(keyword in query_lower for keyword in keywords)

# ===============================
# RESPONSE POST-PROCESSING
# ===============================
def clean_response(text: str) -> str:
    text = re.sub(r"</s>", "", text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text

# ===============================
# MAIN CHATBOT FUNCTION (OPTIMIZED)
# ===============================
def ChatBot(Query, use_streaming=True):
    try:
        messages = load_chatlog()
        # env_query = is_environment_query(Query)
        
        system_messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT}
        ]
        
        # if env_query:
        #     system_messages.append(
        #         {"role": "system", "content": ENVIRONMENT_SYSTEM_PROMPT}
        #     )
        
        system_messages.append(
            {"role": "system", "content": RealtimeInformation()}
        )
        
        messages.append({"role": "user", "content": Query})
        
        # max_tokens = 2048 if env_query else 512
        # temperature = 0.5 if env_query else 0.3
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=system_messages + messages,
            temperature=0.7,
            max_tokens=8192,
            stream=use_streaming,
            top_p=0.9,
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
            print("⚠️ Rate limit reached, clearing chatlog and retrying...")
            save_chatlog([])
            try:
                system_messages = [
                    {"role": "system", "content": BASE_SYSTEM_PROMPT},
                    {"role": "system", "content": RealtimeInformation()}
                ]
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=system_messages + [{"role": "user", "content": Query}],
                    temperature=0.3,
                    max_tokens=512,
                    stream=False
                )
                return clean_response(completion.choices[0].message.content)
            except Exception as retry_error:
                return f"I'm experiencing high load right now. Please try again in a moment."
        
        elif "context" in error_msg or "token" in error_msg:
            print("⚠️ Context too long, clearing chatlog...")
            save_chatlog([])
            return ChatBot(Query, use_streaming=False)
        
        else:
            print(f"❌ Chatbot Error: {e}")
            return "I apologize, but I encountered an error processing your request. Please try rephrasing your question."

# ===============================
# UTILITY FUNCTIONS
# ===============================
def clear_chat_history():
    save_chatlog([])
    print("🧹 Chat history cleared")

def get_chat_stats():
    messages = load_chatlog()
    user_msgs = [m for m in messages if m.get('role') == 'user']
    assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
    return {
        'total_messages': len(messages),
        'user_messages': len(user_msgs),
        'assistant_messages': len(assistant_msgs),
        'last_query': user_msgs[-1]['content'] if user_msgs else None
    }

# ===============================
# BATCH PROCESSING
# ===============================
def batch_chat(queries: list):
    responses = []
    for query in queries:
        response = ChatBot(query, use_streaming=False)
        responses.append({
            'query': query,
            'response': response
        })
    return responses

# ===============================
# CLI ENTRY POINT
# ===============================
if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  {AssistantName} Enhanced Chatbot")
    print(f"  User: {Username}")
    print(f"{'='*60}\n")
    
    print("Commands:")
    print("  - Type your question/query")
    print("  - 'clear' to clear chat history")
    print("  - 'stats' to view statistics")
    print("  - 'exit' to quit\n")
    
    while True:
        try:
            user_input = input(f"{Username} >>> ").strip()
            if not user_input:
                continue
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            if user_input.lower() == 'clear':
                clear_chat_history()
                continue
            if user_input.lower() == 'stats':
                stats = get_chat_stats()
                print(f"\n📊 Chat Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                print()
                continue
            print(f"\n{AssistantName} >>> ", end='', flush=True)
            response = ChatBot(user_input)
            print(response + "\n")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")