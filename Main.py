"""
SARA - Smart Automated Response Assistant
With lazy imports + optimizations + FIXED IMAGE GENERATION INTEGRATION
"""
import re
import shutil
import webbrowser
import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from dotenv import dotenv_values
from datetime import datetime
from Backend.TextToSpeech import TextToSpeech, StopTTS
from Backend.SpeechToText import get_interrupt_query, clear_interrupt_queue, start_interrupt_detection, stop_interrupt_detection
from Backend.TextToSpeech import StopTTS
from Frontend.GUI import SetAssistantStatus
from Backend.System_Automation import SystemAutomation
from Backend.Chatbot import ChatBot
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Frontend.GUI import ShowTextToScreen, SetAssistantStatus
from Backend.TextToSpeech import StopTTS
from Backend.SpeechToText import (
        SpeechRecognition, HotwordDetection, calibrate_microphone,
        start_interrupt_detection, stop_interrupt_detection,
        get_interrupt_query, clear_interrupt_queue
    )
from Frontend.GUI import GraphicalUserInterface, ShowTextToScreen, SetAssistantStatus
from Backend.Model import FirstLayerDMM
from Backend.TextToSpeech import StopTTS
from Frontend.GUI import GraphicalUserInterface

# ==========================================
# IMPORT IMAGE GENERATION MODULE
# ==========================================
from Backend.ImageGeneration import GenerateImages

env_vars = dotenv_values('.env')
AssistantName = env_vars.get('AssistantName', 'SARA')
Username = env_vars.get('Username', 'User')

Path("Data").mkdir(exist_ok=True)
Path("Frontend/Files").mkdir(parents=True, exist_ok=True)

TEMP_DIR = "Frontend/Files"
for file_name, default_content in [
    ("Mic.data", "False"),
    ("Status.data", "Idle"),
    ("Responses.data", ""),
    ("ImageGeneration.data", "False,False"),
    ("snap.data", ""),
    ("snapped_apps.data", "")
]:
    file_path = Path(TEMP_DIR) / file_name
    if not file_path.exists():
        file_path.write_text(default_content)

exit_signal = Path(TEMP_DIR) / "exit.signal"
if exit_signal.exists():
    exit_signal.unlink()

(Path(TEMP_DIR) / "Status.data").write_text("")
(Path(TEMP_DIR) / "Mic.data").write_text("")
(Path(TEMP_DIR) / "Responses.data").write_text("")

print(f"🚀 Initializing {AssistantName}...")

exit_lock = threading.Lock()
should_exit = False
is_speaking = False
last_activity_time = time.time()
is_conversation_active = False
has_greeted_once = False

# Lazy-loaded modules will be imported inside functions

def check_exit_signal():
    if (Path(TEMP_DIR) / "exit.signal").exists():
        (Path(TEMP_DIR) / "exit.signal").unlink()
        return True
    return False

def get_mic_status():
    try:
        return (Path(TEMP_DIR) / "Mic.data").read_text().strip() == "True"
    except:
        return False

def set_mic_status(status: bool):
    try:
        (Path(TEMP_DIR) / "Mic.data").write_text("True" if status else "False")
    except:
        pass

def cleanup_and_exit():
    global should_exit, is_speaking
    print("\n🛑 Shutting down...")
    with exit_lock:
        should_exit = True
        is_speaking = False
    
    # Lazy import here
    
    StopTTS()
    SetAssistantStatus("Shutting down...")
    set_mic_status(False)
    sys.exit(0)

def speak_with_interrupt(text):
    global is_speaking, last_activity_time
    
    if not text or not text.strip():
        return None
    
    with exit_lock:
        is_speaking = True
        clear_interrupt_queue()
    
    start_interrupt_detection()
    
    try:
        interrupt_query = TextToSpeech(text, lambda: is_speaking, lambda: get_interrupt_query())
        last_activity_time = time.time()
        return interrupt_query
    finally:
        with exit_lock:
            is_speaking = False
        stop_interrupt_detection()

# ==========================================
# ENHANCED IMAGE PROMPT EXTRACTION
# ==========================================
def extract_image_prompt(query: str) -> str:
    query = query.lower().strip().rstrip(".?!")

    patterns = [
        r"(?:generate|create|make|draw)\s+(?:an?\s+)?(?:image|picture|photo|drawing)\s+(?:of|for|about)?\s*(.+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1).strip()

    return query


# ==========================================
# TASK EXECUTION WITH FIXED IMAGE GENERATION
# ==========================================
def execute_task(task: str, query: str):
    global last_activity_time
    
    task_lower = task.lower().strip()
    
    # Lazy imports inside function
    
    automation = SystemAutomation()
    
    try:
        if task_lower == "exit":
            response = f"Goodbye {Username}!"
            ShowTextToScreen(response)
            speak_with_interrupt(response)
            cleanup_and_exit()
            return None
        
        # ==========================================
        # IMAGE GENERATION (DIRECT CALL)
        # ==========================================
        elif task_lower.startswith("generate image"):

            prompt = task_lower.replace("generate image", "").strip()

            if not prompt:
                response = "Please tell me what image to generate."
                ShowTextToScreen(response)
                return speak_with_interrupt(response)

            print(f"🎨 Generating image for: {prompt}")

            ShowTextToScreen(f"Generating image: {prompt}")
            speak_with_interrupt(f"Generating image of {prompt}")

            try:
                # DIRECT CALL to your ImageGeneration.py
                GenerateImages(prompt)
                response = "Image generated successfully."
            except Exception as e:
                print("Image generation error:", e)
                response = "Image generation failed."

            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        # ==========================================
        # PRESENTATION CREATION
        # ==========================================
        elif task_lower.startswith("content presentation") and "presentation" in task_lower:
            topic = task.replace("content presentation", "").replace(" presentation", "").strip()
            ShowTextToScreen(f"Creating presentation on: {topic}")
            speak_with_interrupt(f"Creating a presentation on {topic}.")
            response = automation.create_presentation(topic)
            ShowTextToScreen(response)
            return speak_with_interrupt("Presentation created successfully.")
        
        # ==========================================
        # CONTENT WRITING (LETTERS, NOTES, ETC)
        # ==========================================
        elif task_lower.startswith("content "):
            # Handle writing content like letters
            parts = task.replace("content ", "").strip().split(" ", 1)
            content_type = parts[0] if len(parts) > 1 else "letter"
            topic = parts[1] if len(parts) > 1 else parts[0]
            ShowTextToScreen(f"Writing {content_type} on: {topic}")
            speak_with_interrupt(f"Writing a {content_type} on {topic}.")
            response = automation.write_content(topic, content_type)
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        # ==========================================
        # APP MANAGEMENT
        # ==========================================
        elif task.startswith("open "):
            app_name = task.replace("open ", "").strip()
            result = automation.open_app(app_name)
            if isinstance(result, dict):
                ShowTextToScreen(result["display"])
                TextToSpeech(result["speech"])
            else:
                ShowTextToScreen(result)
                TextToSpeech(result)
        
        elif task_lower.startswith("close "):
            app = task.replace("close ", "").strip()
            ShowTextToScreen(f"Closing: {app}")
            response = automation.close_app(app)
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        # ==========================================
        # MEDIA PLAYBACK & SEARCH
        # ==========================================
        elif task_lower.startswith("play "):
            topic = task.replace("play ", "").strip()
            ShowTextToScreen(f"Playing: {topic}")
            response = automation.play_on_youtube(topic)
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        elif task_lower.startswith("google search "):
            search_query = task.replace("google search ", "").strip()
            ShowTextToScreen(f"Searching Google for: {search_query}")
            response = automation.google_search(search_query)
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        elif task_lower.startswith("youtube search "):
            search_query = task.replace("youtube search ", "").strip()
            ShowTextToScreen(f"Searching YouTube for: {search_query}")
            response = automation.youtube_search(search_query)
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        # ==========================================
        # SYSTEM COMMANDS
        # ==========================================
        elif task_lower.startswith("system "):
            sys_cmd = task.replace("system ", "").strip().lower()
            if "set to" in sys_cmd:
                level = sys_cmd.replace("set to ", "").strip()
                ShowTextToScreen(f"Setting volume to: {level}")
                response = automation.set_volume(level)
            elif "mute" in sys_cmd:
                ShowTextToScreen("Muting volume")
                response = automation.mute_volume()
            elif "unmute" in sys_cmd:
                ShowTextToScreen("Unmuting volume")
                response = automation.unmute_volume()
            elif "screenshot" in sys_cmd or "take screenshot" in sys_cmd:
                ShowTextToScreen("Taking screenshot")
                response = automation.take_screenshot()
            elif "record" in sys_cmd or "start screen recording" in sys_cmd:
                ShowTextToScreen("Starting screen recording")
                response = automation.start_screen_recording()
            else:
                response = "Unknown system command."
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        elif task_lower.startswith("run "):
            cmd = task.replace("run ", "").strip()
            ShowTextToScreen(f"Running command: {cmd}")
            # Assuming System_Automation has a run_command method; if not, implement or use subprocess
            try:
                subprocess.run(cmd, shell=True)
                response = f"Executed command: {cmd}"
            except Exception as e:
                response = f"Error executing command: {str(e)}"
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
        
        # ==========================================
        # CHATBOT & REALTIME SEARCH
        # ==========================================
        elif task_lower.startswith("general "):
            q = task.replace("general ", "").strip()
            ShowTextToScreen(f"Processing: {q}")
            response = ChatBot(q)
            ShowTextToScreen(response)  # Then update GUI
            interrupt = speak_with_interrupt(response)  # Speak first
            return interrupt
        
        elif task_lower.startswith("realtime "):
            q = task.replace("realtime ", "").strip()
            ShowTextToScreen(f"Searching realtime: {q}")
            response = RealtimeSearchEngine(q)
            ShowTextToScreen(response)  # Then update GUI
            interrupt = speak_with_interrupt(response)  # Speak first
            return interrupt
        
        # ==========================================
        # DEFAULT: CHATBOT
        # ==========================================
        else:
            response = ChatBot(query)
            ShowTextToScreen(response)
            return speak_with_interrupt(response)
            
    except Exception as e:
        msg = f"Error: {str(e)}"
        print(f"❌ {msg}")
        ShowTextToScreen(msg)
        return speak_with_interrupt("Sorry, something went wrong.")

def assistant_loop():
    global should_exit, last_activity_time, is_conversation_active, has_greeted_once
    
    if check_exit_signal():
        cleanup_and_exit()
    
    print(f"✅ {AssistantName} ready!")
    
    # Lazy imports
    
    
    try:
        calibrate_microphone()
    except Exception as e:
        print(f"Mic calibration failed: {e}")
    
    while not should_exit:
        try:
            if check_exit_signal():
                cleanup_and_exit()
                break
            
            if get_mic_status():
                if time.time() - last_activity_time > 10:
                    SetAssistantStatus("💤 Standby...")
                    set_mic_status(False)
                    is_conversation_active = False
                    clear_interrupt_queue()
                    continue
            
            if not get_mic_status():
                SetAssistantStatus(f"Say 'Ok {AssistantName}'...")
                activated = HotwordDetection()
                
                if activated:
                    set_mic_status(True)
                    is_conversation_active = True
                    last_activity_time = time.time()
                    
                    if not has_greeted_once:
                        greeting = f"Hello {Username}! How can i help you today?"
                        ShowTextToScreen(greeting)
                        speak_with_interrupt(f"Hello {Username}. How can i help you today?")
                        has_greeted_once = True
                
                continue
            
            SetAssistantStatus("🎤 Listening...")
            query = SpeechRecognition(timeout=5, phrase_limit=10)  # Increased phrase_limit
            
            if not query or not query.strip():
                time.sleep(0.03)
                continue
            
            last_activity_time = time.time()
            StopTTS()
            
            print(f"\n🗣️ User: {query}")
            ShowTextToScreen(f"You: {query}")
            
            SetAssistantStatus("🧠 Processing...")
            tasks = FirstLayerDMM(query)
            
            print(f"🎯 Tasks: {tasks}")
            
            # In Main.py -> assistant_loop

            for task in tasks:
                if should_exit:
                    break
                # FIX: Pass 'task' as both the intent and the specific query for that task
                # This prevents the execution from falling back to the full original 'query'
                interrupt = execute_task(task, task) 
                
                if interrupt:
                    new_tasks = FirstLayerDMM(interrupt)
                    for nt in new_tasks:
                        execute_task(nt, nt)
                    break
                time.sleep(0.08)
            
            clear_interrupt_queue()
            time.sleep(0.03)
        
        except KeyboardInterrupt:
            cleanup_and_exit()
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(0.4)

def main():
    print("="*60)
    print(f"  {AssistantName} - Optimized Version (Image Gen Fixed)")
    print("="*60 + "\n")
    
    assistant_thread = threading.Thread(target=assistant_loop, daemon=True)
    assistant_thread.start()
    
    try:
        
        GraphicalUserInterface()
    except KeyboardInterrupt:
        cleanup_and_exit()

if __name__ == "__main__":
    main()