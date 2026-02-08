import re
from System_Automation import SystemAutomation

automation = SystemAutomation()


def handle_query(query: str):
    q = query.lower().strip()

    # ===== IMAGE GENERATION (HIGHEST PRIORITY) =====
    if any(word in q for word in ["generate image", "create image", "make image", "draw image", "generate picture", "create picture"]):
        return f"image {query}"

    # 1. YOUTUBE PLAYBACK (Highest Priority)
    if q.startswith("play "):
        topic = q.replace("play ", "").replace("on youtube", "").strip()
        return automation.play_on_youtube(topic)

    # 2. SPECIFIC SEARCHES
    if "on youtube" in q:
        topic = q.replace("search for", "").replace("search", "").replace("on youtube", "").strip()
        return automation.youtube_search(topic)
    
    if "on google" in q:
        topic = q.replace("search for", "").replace("search", "").replace("on google", "").strip()
        return automation.google_search(topic)

    # 3. GENERIC SEARCH (Catches "search for {topic}")
    if q.startswith("search for ") or q.startswith("search "):
        topic = q.replace("search for ", "").replace("search ", "").strip()
        return automation.google_search(topic)

    # 4. POWERPOINT (Now specific to "create" to avoid search conflicts)
    if "create" in q and ("ppt" in q or "presentation" in q):
        topic = q.replace("create", "").replace("ppt", "").replace("presentation", "").strip()
        return automation.create_presentation(topic)

    # 5. OPEN / CLOSE
    if q.startswith("open "):
        return automation.open_app(q.replace("open ", "").strip())

    # ===== EXIT =====
    if q in ["exit", "quit", "bye"]:
        return "Goodbye!"

    # ===== WHO ARE YOU =====
    if "who are you" in q or "what can you do" in q:
        return (
            "I am a Voice assistant names SARA\n"
            "I can:\n"
            "- Open or close apps\n"
            "- Control volume\n"
            "- Create PowerPoint presentations\n"
            "- Write letters, essays, songs\n"
            "- Minimize or maximize windows"
        )

    # ===== VOLUME =====
    if "mute" == q:
        return automation.mute_volume()

    if "unmute" == q:
        return automation.unmute_volume()

    if "volume" in q:
        match = re.search(r"(\d+)", q)
        if match:
            return automation.set_volume(match.group(1))
        
    # ===== NEW: YOUTUBE & GOOGLE (PRIORITIZED) =====
    if "play" in q and "on youtube" in q:
        topic = q.replace("play", "").replace("on youtube", "").strip()
        return automation.play_on_youtube(topic)
    
    if "search" in q and "on youtube" in q:
        topic = q.replace("search", "").replace("on youtube", "").strip()
        return automation.youtube_search(topic)

    if "google search" in q or (q.startswith("search") and "on google" in q):
        topic = q.replace("google search", "").replace("search", "").replace("on google", "").strip()
        return automation.google_search(topic)

    # ===== OPEN / CLOSE =====
    if q.startswith("open "):
        return automation.open_app(q.replace("open ", ""))

    if q.startswith("close "):
        return automation.close_app(q.replace("close ", ""))

    # ===== WINDOW CONTROL =====
    if "minimize all" in q:
        return automation.minimize_all_windows()

    if q.startswith("minimize "):
        return automation.minimize_app(q.replace("minimize ", ""))

    if q.startswith("maximize "):
        return automation.maximize_app(q.replace("maximize ", ""))
    
    # Add this inside handle_query(query) in router.py

    # ===== SCREENSHOT =====

    if "screenshot" in q or "capture screen" in q:
        return automation.take_screenshot()

    # 1. RECORDING & SCREENSHOT
    if any(word in q for word in ["record", "record screen", "screen record", "recording", "start recording", "screen recording"]):
        return automation.start_screen_recording()
    # ===== WRITE CONTENT =====
    if q.startswith("write "):
        content = q.replace("write ", "")
        if "letter" in q:
            return automation.generate_and_write_content(content, "letter")
        if "essay" in q:
            return automation.generate_and_write_content(content, "essay")
        if "song" in q:
            return automation.generate_and_write_content(content, "song")
        return automation.generate_and_write_content(content, "text")

    # ===== POWERPOINT (NOW LOWER PRIORITY TO PREVENT FALSE TRIGGERS) =====
    if ("ppt" in q or "presentation" in q) and "search" not in q:
        topic = q.replace("create", "").replace("ppt", "").replace("presentation", "")
        return automation.create_presentation(topic.strip())

    return "I don't know how to do that yet."
