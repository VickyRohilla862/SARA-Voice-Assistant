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

funcs = ['exit', 'general', 'realtime', 'open', 'close', 'play', 'generate image', 'system', 'content', 'google search', 'youtube search', 'reminder']

# Rate limiting
last_api_call = 0
MIN_API_INTERVAL = 3  # Minimum 3 seconds between API calls

def LocalDecisionMaker(prompt: str):
    """
    Fast local pattern matching - NO API CALLS!
    Returns decision immediately based on keywords.
    """
    prompt_lower = prompt.lower().strip()
    
    # EXIT patterns
    if any(word in prompt_lower for word in ['bye', 'goodbye', 'exit', 'quit', 'see you']):
        return ['exit']
    
    # OPEN patterns
    open_match = re.search(r'\bopen\s+(\w+(?:\s+\w+)?)', prompt_lower)
    if open_match:
        apps = re.findall(r'\bopen\s+(\w+(?:\s+\w+)?)', prompt_lower)
        return [f'open {app}' for app in apps]
    
    # CLOSE patterns
    close_match = re.search(r'\bclose\s+(\w+(?:\s+\w+)?)', prompt_lower)
    if close_match:
        apps = re.findall(r'\bclose\s+(\w+(?:\s+\w+)?)', prompt_lower)
        return [f'close {app}' for app in apps]
    
    # PLAY patterns
    if 'play' in prompt_lower and not 'display' in prompt_lower:
        song = prompt_lower.replace('play', '').strip()
        if song:
            return [f'play {song}']
    
    # GENERATE IMAGE patterns
    if any(phrase in prompt_lower for phrase in ['generate image', 'create image', 'make image', 'draw image']):
        img_prompt = re.sub(r'(generate|create|make|draw)\s+(an?\s+)?image\s+(of\s+)?', '', prompt_lower).strip()
        if img_prompt:
            return [f'generate image {img_prompt}']
    
    # ✅ VOLUME/SYSTEM patterns - FIXED WITH FLEXIBLE REGEX
    if any(word in prompt_lower for word in ['mute', 'unmute', 'volume']):
        # Extract volume level if present
        level_match = re.search(r'(\d{1,3})', prompt_lower)
        
        # SET/TURN volume patterns (flexible with "the", "to", "my", etc.)
        # .{0,10} allows 0-10 characters between words (handles "turn THE volume TO 100")
        if re.search(r'(set|turn|make|change).{0,10}volume.{0,10}\d', prompt_lower):
            if level_match:
                return [f'system set volume {level_match.group(1)}']
        
        # INCREASE/RAISE volume patterns
        elif re.search(r'(increase|raise|up|louder).{0,10}volume', prompt_lower):
            amount = level_match.group(1) if level_match else '10'
            return [f'system increase volume {amount}']
        
        # DECREASE/LOWER volume patterns
        elif re.search(r'(decrease|lower|down|reduce|quieter).{0,10}volume', prompt_lower):
            amount = level_match.group(1) if level_match else '10'
            return [f'system decrease volume {amount}']
        
        # Simple VOLUME UP/DOWN
        elif 'volume up' in prompt_lower:
            return ['system volume up']
        elif 'volume down' in prompt_lower:
            return ['system volume down']
        
        # MUTE/UNMUTE
        elif 'mute' in prompt_lower and 'unmute' not in prompt_lower:
            return ['system mute']
        elif 'unmute' in prompt_lower:
            return ['system unmute']
    
    # CONTENT/WRITING patterns
    if any(word in prompt_lower for word in ['write', 'create', 'compose', 'draft']):
        if any(word in prompt_lower for word in ['letter', 'email', 'essay', 'application', 'poem', 'story', 'code', 'song', 'script', 'article', 'report', 'document', 'speech', 'presentation']):
            content_topic = re.sub(r'(write|create|compose|draft)\s+(a|an|me)?\s*', '', prompt_lower).strip()
            return [f'content {content_topic}']
    
    # REALTIME patterns - CHECK FIRST for shopping/current info queries
    # This must come BEFORE generic search patterns!
    realtime_keywords = [
        'who is', 'what is', 'tell me about', 'news', 'weather', 'current',
        'today', 'latest', 'recent', 'now', 'prime minister', 'president',
        'ceo', 'update', 'stock price', 'headlines', 'best', 'top', 'compare',
        'buy', 'purchase', 'price of', 'cost of', 'review', 'rating', 'recommend'
    ]
    
    if any(keyword in prompt_lower for keyword in realtime_keywords):
        # Check if asking about a specific person or current topic
        if re.search(r'\b(who is|what is|tell me about)\s+\w+', prompt_lower):
            return [f'realtime {prompt}']
        if any(word in prompt_lower for word in ['news', 'weather', 'today', 'current', 'latest', 'headlines']):
            return [f'realtime {prompt}']
        # Shopping/product queries (best laptop, top phones, etc.)
        if any(word in prompt_lower for word in ['best', 'top', 'compare', 'buy', 'purchase', 'review', 'recommend', 'price', 'cost']):
            return [f'realtime {prompt}']
    
    # GOOGLE SEARCH patterns - AFTER realtime check
    if 'google search' in prompt_lower or 'search google' in prompt_lower or 'search on google' in prompt_lower:
        topic = re.sub(r'(google\s+)?search(\s+on)?\s+(google\s+)?(for\s+)?', '', prompt_lower).strip()
        if topic:
            return [f'google search {topic}']
    
    # Generic SEARCH patterns (only for non-shopping searches)
    if prompt_lower.startswith('search for') or prompt_lower.startswith('search about') or ' search for ' in prompt_lower:
        # Extract the topic
        topic = re.sub(r'search\s+(for|about)\s+', '', prompt_lower).strip()
        # If it contains shopping keywords, it should have been caught by realtime already
        # So this is for informational searches only
        if topic:
            return [f'google search {topic}']
    
    # YOUTUBE SEARCH patterns
    if 'youtube search' in prompt_lower or 'search youtube' in prompt_lower or 'search on youtube' in prompt_lower:
        topic = re.sub(r'(youtube\s+)?search(\s+on)?\s+(youtube\s+)?(for\s+)?', '', prompt_lower).strip()
        if topic:
            return [f'youtube search {topic}']
    
    # Questions about time/date (handled by general with realtime info)
    if any(word in prompt_lower for word in ['time', 'date', 'day', 'month', 'year']):
        if any(word in prompt_lower for word in ['what', 'tell', 'show']):
            return [f'general {prompt}']
    
    # DEFAULT: General query
    return [f'general {prompt}']


def APIDecisionMaker(prompt: str):
    """
    Uses Cohere API for complex decision making.
    Only called if rate limit allows.
    """
    global last_api_call
    
    preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write an application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a LLM model (conversational AI chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.', if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it requires up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query cannot be answered by a LLM model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual or thing like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', etc.
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate an image with given prompt like 'generate image of a lion', 'generate image of a cat', etc. but if the query is asking to generate multiple images, respond with 'generate image 1st image prompt, generate image 2nd image prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, volume down, etc. but if the query is asking to do multiple tasks, respond with 'system 1st task, system 2nd task', etc.
-> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
-> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
-> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search multiple topics on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye jarvis.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

    ChatHistory = [
        {'role': 'user', 'message': 'how are you'},
        {'role': 'chatbot', 'message': 'general how are you'},
        {'role': 'user', 'message': 'do you like pizza?'},
        {'role': 'chatbot', 'message': 'general do you like pizza?'},
        {'role': 'user', 'message': 'open chrome and tell me about mahatma gandhi'},
        {'role': 'chatbot', 'message': 'open chrome, general tell me about mahatma gandhi'},
        {'role': 'user', 'message': 'open chrome and firefox'},
        {'role': 'chatbot', 'message': 'open chrome, open firefox'},
    ]
    
    try:
        stream = co.chat_stream(
            model='command-r-plus-08-2024',
            message=prompt,
            temperature=0.7,
            chat_history=ChatHistory,
            prompt_truncation='OFF',
            connectors=[],
            preamble=preamble
        )

        response = ""
        for event in stream:
            if event.event_type == 'text-generation':
                response += event.text
        
        last_api_call = time.time()
        
        # Process response
        response = response.replace('\n', '').split(',')
        response = [i.strip() for i in response]
        
        temp = []
        for task in response:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)
                    break
        
        if temp and '(query)' not in str(temp):
            return temp
        
    except TooManyRequestsError:
        print("⚠️ API Rate limit - using local decision maker")
    except Exception as e:
        print(f"⚠️ API Error: {e} - using local decision maker")
    
    return None


def FirstLayerDMM(prompt: str = 'test'):
    """
    Main decision maker - tries LOCAL first, only uses API for ambiguous cases.
    """
    global last_api_call
    
    if not prompt or len(prompt.strip()) < 2:
        return ['general hello']
    
    # First, try LOCAL pattern matching (instant, no API)
    local_decision = LocalDecisionMaker(prompt)
    
    # ✅ ALWAYS use local decision for these types (never override with API):
    priority_types = ['open', 'close', 'play', 'system', 'generate image', 
                      'content', 'google search', 'youtube search', 'exit', 'realtime']
    
    if local_decision and local_decision[0]:
        # Check if it's a priority type
        if any(local_decision[0].startswith(ptype) for ptype in priority_types):
            print(f"✅ Local Decision (Priority): {local_decision}")
            return local_decision
    
    # For ONLY "general" queries, consider asking API (if rate limit allows)
    if local_decision[0].startswith('general'):
        time_since_last_call = time.time() - last_api_call
        if time_since_last_call >= MIN_API_INTERVAL:
            print("🔄 Checking with API for general query...")
            api_decision = APIDecisionMaker(prompt)
            if api_decision:
                print(f"✅ API Decision: {api_decision}")
                return api_decision
        else:
            wait_time = MIN_API_INTERVAL - time_since_last_call
            print(f"⏳ Rate limit: using local decision")
    
    # Fallback: use local decision
    print(f"✅ Using Local Decision: {local_decision}")
    return local_decision


if __name__ == "__main__":
    # Test cases
    test_queries = [
        "open chrome",
        "close chrome",
        "play shakira hindi on youtube",
        "what is the weather outside",
        "generate image of santa clause",
        "write a code to hack wifi",
        'turn the volume to 100',
        'decrease the volume by 20',
        'increase the volume by 10',
        'mute the device',
        'unmute the device',
        'what is the current price of lenovo loq on flipkart',
        'how are you'
    ]
    
    print("Testing Decision Maker:\n")
    for query in test_queries:
        print(f"Query: {query}")
        result = FirstLayerDMM(query)
        print(f"Decision: {result}\n")
        time.sleep(0.5)
