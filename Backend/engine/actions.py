import os

def set_volume(volume):
    if volume is None:
        return "Please specify a volume level."

    volume = int(volume)
    volume = max(0, min(100, volume))

    # Windows example (safe)
    os.system(f"nircmd.exe setsysvolume {int(volume * 655.35)}")

    return f"Volume set to {volume}%"

def create_ppt(topic):
    if not topic:
        return "Please tell me the presentation topic."

    # Placeholder logic (can be expanded)
    return f"PowerPoint presentation generated for topic: {topic}"
