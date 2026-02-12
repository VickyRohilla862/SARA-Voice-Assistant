import speech_recognition as sr
import mtranslate as mt
from dotenv import dotenv_values
import time
import sys
import os
import threading
import queue
from difflib import SequenceMatcher
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Frontend.GUI import SetAssistantStatus
from Backend.TextToSpeech import StopTTS

# Load env
env = dotenv_values(".env")
INPUT_LANG = env.get("InputLanguage", "en-IN")

# ==========================================
# ENHANCED RECOGNIZER WITH AUDIO PREPROCESSING
# ==========================================
recognizer = sr.Recognizer()

# OPTIMIZED SETTINGS FOR MAXIMUM ACCURACY
recognizer.energy_threshold = 300  # Better baseline
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15  # More responsive
recognizer.dynamic_energy_ratio = 1.5  # Better signal detection
recognizer.pause_threshold = 1.2  # INCREASED: Wait longer before considering speech complete
recognizer.phrase_threshold = 0.3  # Quick phrase detection
recognizer.non_speaking_duration = 1.0  # INCREASED: Wait longer for continuation

def calibrate_microphone():
    """Advanced microphone calibration with multi-pass noise profiling"""
    try:
        with sr.Microphone(sample_rate=16000) as source:
            print("🎚️ Calibrating microphone (this may take a moment)...")
            # Extended calibration for better noise baseline
            recognizer.adjust_for_ambient_noise(source, duration=2.0)
            print(f"🎚️ Microphone calibrated (threshold: {recognizer.energy_threshold:.0f})")
            print(f"🎚️ Sample rate: {source.SAMPLE_RATE} Hz")
    except Exception as e:
        print(f"⚠️ Calibration error: {e}")
        print("Continuing with default settings...")

HOTWORDS = ["hey sarah", "hey sara", "ok sarah", "ok sara", 
            "hey saraah", "hey sarrah", "ok saraah", "ok sarrah",
            "hey sora", "ok sora", "hey sarra", "ok sarra",
            "a sarah", "a sara", "hey sir", "ok sir", "ok"]

# ==========================================
# COMPREHENSIVE PHRASE CORRECTION SYSTEM
# ==========================================
COMMON_CORRECTIONS = {
    # Common misrecognitions
    "hu r u": "who are you",
    "hu ru": "who are you",
    "who ru": "who are you",
    "hu are you": "who are you",
    "hoo are you": "who are you",
    "wat is": "what is",
    "wats": "what's",
    "wat": "what",
    "hw to": "how to",
    "tel me": "tell me",
    "opn": "open",
    "cls": "close",
    "ply": "play",
    "serch": "search",
    "gogle": "google",
    "youtub": "youtube",
    "youtube": "youtube",
    "increse": "increase",
    "decrese": "decrease",
    "volum": "volume",
    "creat": "create",
    "ppt": "ppt",
    "on ai": "on ai",
    "opn krom": "open chrome",
    "open krom": "open chrome",
    "spotify": "spotify",
    "spotty": "spotify",
    "spotify": "spotify",
    "crom": "chrome",
    "krome": "chrome",
    "chrome": "chrome",
    "kroom": "chrome",
    "vs code": "vs code",
    "visual studio": "vs code",
    "notepad": "notepad",
    "calculator": "calculator",
    "weather": "weather",
    "whether": "weather",
    "wether": "weather",
    "time": "time",
    "tym": "time",
    "date": "date",
    "dat": "date",
    "send": "send",
    "massage": "message",
    "massege": "message",
    "whatsapp": "whatsapp",
    "watts up": "whatsapp",
    "watsapp": "whatsapp",
    "email": "email",
    "gmail": "gmail",
    "g mail": "gmail",
    "turn on": "turn on",
    "turn off": "turn off",
    "shut down": "shutdown",
    "restart": "restart",
    "sleep": "sleep",
    "minimize": "minimize",
    "maximize": "maximize",
    "screenshot": "screenshot",
    "screen shot": "screenshot",
}

# Word-level corrections for better fuzzy matching
WORD_CORRECTIONS = {
    "opn": "open", "cls": "close", "ply": "play",
    "crom": "chrome", "krome": "chrome", "kroom": "chrome",
    "gogle": "google", "googel": "google",
    "youtub": "youtube", "u tube": "youtube",
    "spotify": "spotify", "spotty": "spotify",
    "volum": "volume", "vollume": "volume",
    "wat": "what", "wats": "what's",
    "hw": "how", "haw": "how",
    "tel": "tell", "till": "tell",
    "serch": "search", "surch": "search",
    "creat": "create", "craete": "create",
    "ppt": "ppt", "pp": "ppt",
    "increse": "increase", "decrese": "decrease",
    "massege": "message", "massage": "message",
    "watsapp": "whatsapp", "watts": "whatsapp",
}

def fuzzy_correct(text):
    """Enhanced fuzzy matching with multi-level correction"""
    if not text:
        return text
    
    text_lower = text.lower().strip()
    
    # Level 1: Direct phrase correction
    if text_lower in COMMON_CORRECTIONS:
        return COMMON_CORRECTIONS[text_lower]
    
    # Level 2: Word-by-word correction
    words = text_lower.split()
    corrected_words = []
    
    for word in words:
        # Direct word correction
        if word in WORD_CORRECTIONS:
            corrected_words.append(WORD_CORRECTIONS[word])
        elif word in COMMON_CORRECTIONS:
            corrected_words.append(COMMON_CORRECTIONS[word])
        else:
            # Level 3: Fuzzy match against known corrections
            best_match = word
            best_ratio = 0.80  # Higher threshold for better accuracy
            
            # Check word corrections first
            for wrong, correct in WORD_CORRECTIONS.items():
                ratio = SequenceMatcher(None, word, wrong).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = correct
            
            corrected_words.append(best_match)
    
    # Level 4: Check if corrected phrase exists in phrase corrections
    corrected_text = ' '.join(corrected_words)
    if corrected_text in COMMON_CORRECTIONS:
        return COMMON_CORRECTIONS[corrected_text]
    
    return corrected_text

# ==========================================
# AUDIO PREPROCESSING FOR BETTER RECOGNITION
# ==========================================
def preprocess_audio(audio_data):
    """
    Apply audio preprocessing to improve recognition accuracy
    """
    try:
        # Convert to numpy array for processing
        audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
        
        # Normalize audio levels
        if audio_array.max() > 0:
            audio_array = audio_array.astype(np.float32)
            audio_array = audio_array / np.abs(audio_array).max()
            audio_array = (audio_array * 32767).astype(np.int16)
        
        # Convert back to AudioData
        processed_audio = sr.AudioData(
            audio_array.tobytes(),
            audio_data.sample_rate,
            audio_data.sample_width
        )
        
        return processed_audio
    except Exception as e:
        print(f"⚠️ Audio preprocessing error: {e}")
        return audio_data  # Return original if processing fails

# ==========================================
# INTERRUPT DETECTION SYSTEM
# ==========================================
interrupt_listener = None
interrupt_query_queue = queue.Queue()
interrupt_lock = threading.Lock()
interrupt_active = False

def start_interrupt_detection():
    """Enhanced interrupt detection with preprocessing"""
    global interrupt_listener, interrupt_active
    
    with interrupt_lock:
        if interrupt_listener is not None:
            return
        interrupt_active = True
    
    def interrupt_callback(recognizer_instance, audio):
        global interrupt_active
        
        if not interrupt_active:
            return
        
        try:
            # Preprocess audio
            processed_audio = preprocess_audio(audio)
            
            # Try recognition with shorter timeout
            text = recognizer_instance.recognize_google(
                processed_audio, 
                language=INPUT_LANG,
                show_all=False
            )
            
            if text and text.strip():
                corrected = fuzzy_correct(text)
                processed_query = QueryModifier(corrected)
                
                print(f"🎤 User interrupted with: {processed_query}")
                
                # Clear queue and add new interrupt
                while not interrupt_query_queue.empty():
                    try:
                        interrupt_query_queue.get_nowait()
                    except queue.Empty:
                        break
                
                interrupt_query_queue.put(processed_query)
                StopTTS()
                
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"⚠️ Recognition service error: {e}")
        except Exception as e:
            print(f"⚠️ Interrupt detection error: {e}")
    
    try:
        mic = sr.Microphone(sample_rate=16000)
        interrupt_listener = recognizer.listen_in_background(
            mic,
            interrupt_callback,
            phrase_time_limit=5
        )
        print("👂 Interrupt detection started")
    except Exception as e:
        print(f"⚠️ Failed to start interrupt detection: {e}")
        interrupt_active = False

def stop_interrupt_detection():
    """Stop interrupt detection with proper cleanup"""
    global interrupt_listener, interrupt_active
    
    with interrupt_lock:
        interrupt_active = False
        
        if interrupt_listener is not None:
            try:
                interrupt_listener(wait_for_stop=False)
                time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Error stopping interrupt listener: {e}")
            finally:
                interrupt_listener = None
    
    print("🔇 Interrupt detection stopped")

def get_interrupt_query():
    """Get the query that interrupted (non-blocking)"""
    try:
        return interrupt_query_queue.get_nowait()
    except queue.Empty:
        return None

def clear_interrupt_queue():
    """Clear all pending interrupt queries"""
    while not interrupt_query_queue.empty():
        try:
            interrupt_query_queue.get_nowait()
        except queue.Empty:
            break

# ==========================================
# ENHANCED QUERY PROCESSING
# ==========================================
def QueryModifier(text):
    """Enhanced query modifier with better formatting and grammar"""
    if not text:
        return None
    
    text = text.strip()
    
    # Apply all corrections
    text = fuzzy_correct(text)
    
    # Remove extra spaces and clean up
    text = ' '.join(text.split())
    
    if not text:
        return None
    
    # Question detection
    question_words = (
        "how", "what", "who", "where", "when",
        "why", "which", "can you", "could you", "would you",
        "will you", "should", "is", "are", "do", "does",
        "what's", "where's", "when's", "who's", "how's"
    )
    
    text_lower = text.lower()
    
    # Format as question or statement
    if any(text_lower.startswith(q) for q in question_words) or text_lower.endswith('?'):
        result = text.capitalize()
        if not result.endswith('?'):
            result += '?'
        return result
    else:
        result = text.capitalize()
        if not result.endswith('.'):
            result += '.'
        return result

def UniversalTranslator(text):
    """Enhanced translator with error handling"""
    try:
        translated = mt.translate(text, "en", "auto")
        return translated.capitalize()
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return text.capitalize()

# ==========================================
# MULTI-ATTEMPT SPEECH RECOGNITION
# ==========================================
def SpeechRecognition(timeout=5, phrase_limit=10, retry_count=2):
    """
    Enhanced speech recognition with:
    - Audio preprocessing
    - Multiple recognition attempts
    - Better error handling
    - Adaptive timeout
    - INCREASED phrase_limit to capture complete sentences
    """
    SetAssistantStatus("🎤 Listening...")
    
    for attempt in range(retry_count):
        try:
            with sr.Microphone(sample_rate=16000) as source:
                StopTTS()
                
                # Quick ambient adjustment on first attempt
                if attempt == 0:
                    recognizer.adjust_for_ambient_noise(source, duration=0.4)
                
                try:
                    # Listen with extended timeout on retries
                    # INCREASED phrase_limit to capture longer, complete sentences
                    current_timeout = timeout if attempt == 0 else timeout + 2
                    current_phrase_limit = phrase_limit if attempt == 0 else phrase_limit + 3
                    
                    audio = recognizer.listen(
                        source,
                        timeout=current_timeout,
                        phrase_time_limit=current_phrase_limit
                    )
                except sr.WaitTimeoutError:
                    if attempt < retry_count - 1:
                        print(f"⏱️ Timeout, retrying... ({attempt + 1}/{retry_count})")
                        SetAssistantStatus("⏱️ Timeout, please try again...")
                        continue
                    return None
            
            SetAssistantStatus("⏳ Processing...")
            
            try:
                # Preprocess audio for better recognition
                processed_audio = preprocess_audio(audio)
                
                # Primary recognition with Google
                text = recognizer.recognize_google(
                    processed_audio, 
                    language=INPUT_LANG,
                    show_all=False
                )
                
                print(f"🔍 Raw recognized: '{text}'")
                
                if not text or not text.strip():
                    raise sr.UnknownValueError()
                
                # Check if sentence seems incomplete (ends with preposition/incomplete phrase)
                incomplete_indicators = ['on', 'of', 'in', 'at', 'to', 'for', 'with', 'about', 'a', 'an', 'the']
                words = text.strip().split()
                
                if len(words) > 0 and words[-1].lower() in incomplete_indicators:
                    print(f"⚠️ Incomplete phrase detected (ends with '{words[-1]}')")
                    if attempt < retry_count - 1:
                        print(f"🔄 Requesting continuation...")
                        SetAssistantStatus("🎤 Please continue or repeat...")
                        time.sleep(0.3)
                        continue
                
                # Apply corrections
                corrected = fuzzy_correct(text)
                print(f"✨ After correction: '{corrected}'")
                
                # Process and return
                if INPUT_LANG.lower().startswith("en"):
                    result = QueryModifier(corrected)
                else:
                    result = QueryModifier(UniversalTranslator(corrected))
                
                if result:
                    print(f"✅ Final output: '{result}'")
                    return result
                else:
                    raise sr.UnknownValueError()
            
            except sr.UnknownValueError:
                if attempt < retry_count - 1:
                    print(f"❓ Could not understand, retrying... ({attempt + 1}/{retry_count})")
                    SetAssistantStatus("❓ Didn't catch that, please repeat...")
                    time.sleep(0.5)
                    continue
                print("❌ Could not understand audio after all retries")
                return None
            
            except sr.RequestError as e:
                print(f"❌ Recognition service error: {e}")
                if attempt < retry_count - 1:
                    time.sleep(0.5)
                    continue
                return None
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            if attempt < retry_count - 1:
                time.sleep(0.3)
                continue
            return None
    
    return None

# ==========================================
# ENHANCED HOTWORD DETECTION
# ==========================================
def HotwordDetection():
    """
    Enhanced hotword detection with:
    - Better noise adaptation
    - Fuzzy matching for variations
    - More reliable detection
    """
    SetAssistantStatus("👂 Waiting for 'Ok Sara...'")
    
    detection_count = 0
    
    with sr.Microphone(sample_rate=16000) as source:
        # Initial calibration
        print("🎚️ Calibrating for hotword detection...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        while True:
            try:
                # Listen for hotword
                audio = recognizer.listen(
                    source,
                    timeout=2.0,
                    phrase_time_limit=4  # INCREASED: Allow longer activation phrases
                )
                
                # Preprocess audio
                processed_audio = preprocess_audio(audio)
                
                # Recognize
                text = recognizer.recognize_google(
                    processed_audio, 
                    language=INPUT_LANG
                ).lower().strip()
                
                detection_count += 1
                print(f"🔍 Hotword check #{detection_count}: '{text}'")
                
                # Direct match
                if any(hotword in text for hotword in HOTWORDS):
                    print(f"✅ Hotword detected: '{text}'")
                    SetAssistantStatus("🎤 Activated! Listening...")
                    from Frontend.GUI import SetMicrophoneStatus
                    SetMicrophoneStatus('True')
                    return True
                
                # Fuzzy match for variations
                for hotword in HOTWORDS:
                    ratio = SequenceMatcher(None, text, hotword).ratio()
                    if ratio > 0.72:  # Threshold for fuzzy matching
                        print(f"✅ Fuzzy matched '{text}' to '{hotword}' (similarity: {ratio:.2f})")
                        SetAssistantStatus("🎤 Activated! Listening...")
                        from Frontend.GUI import SetMicrophoneStatus
                        SetMicrophoneStatus('True')
                        return True
            
            except sr.WaitTimeoutError:
                # Normal - just listening
                pass
            
            except sr.UnknownValueError:
                # Couldn't understand - might be noise or too quiet
                pass
            
            except sr.RequestError as e:
                print(f"❌ Hotword detection service error: {e}")
                time.sleep(1)
            
            except Exception as e:
                print(f"❌ Hotword detection error: {e}")
                time.sleep(0.2)

# ==========================================
# TESTING SECTION
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎤 TESTING ENHANCED SPEECH RECOGNITION SYSTEM")
    print("=" * 60)
    
    calibrate_microphone()
    
    print("\n" + "=" * 60)
    print("TEST 1: HOTWORD DETECTION")
    print("=" * 60)
    print("📢 Say 'Ok Sara'...")
    HotwordDetection()
    print("✅ Hotword detected successfully!\n")
    
    print("=" * 60)
    print("TEST 2: SPEECH RECOGNITION")
    print("=" * 60)
    print("📢 Performing 3 recognition tests. Say something each time...\n")
    
    for i in range(3):
        print(f"\n--- Test {i+1}/3 ---")
        text = SpeechRecognition()
        if text:
            print(f"✅ RECOGNIZED: {text}")
        else:
            print("❌ No speech detected or couldn't understand")
        
        if i < 2:
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎉 TESTING COMPLETE")
<<<<<<< HEAD
    print("=" * 60)
=======
    print("=" * 60)
>>>>>>> 3f7e11d900acadde38fd561f6d620bf0b777ade8
