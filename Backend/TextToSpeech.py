import os
import uuid
import pygame
import asyncio
import edge_tts
import threading
import re
import queue
from unidecode import unidecode
from dotenv import dotenv_values
import time
from io import BytesIO
from langdetect import detect, LangDetectException


# =====================
# ENV
# =====================
env = dotenv_values(".env")

EN_VOICE = "en-IN-NeerjaNeural"
HI_VOICE = "hi-IN-SwaraNeural"

VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",      # Female (English - India)
    "hi": "hi-IN-SwaraNeural",       # Female (Hindi)
    "es": "es-ES-ElviraNeural",      # Female (Spanish - Spain)
    "fr": "fr-FR-DeniseNeural",      # Female (French - France)
    "de": "de-DE-KatjaNeural",       # Female (German - Germany)
    "it": "it-IT-ElsaNeural",        # Female (Italian - Italy)
    "pt": "pt-BR-FranciscaNeural",   # Female (Portuguese - Brazil)
    "ru": "ru-RU-SvetlanaNeural",    # Female (Russian)
    "ja": "ja-JP-NanamiNeural",      # Female (Japanese)
    "ko": "ko-KR-SunHiNeural",       # Female (Korean)
    "zh-cn": "zh-CN-XiaoxiaoNeural", # Female (Chinese - Simplified)
    "ar": "ar-SA-ZariyahNeural",     # Female (Arabic - Saudi Arabia)
    "bn": "bn-IN-TanishaaNeural",    # Female (Bengali - India, added)
    "gu": "gu-IN-DhwaniNeural",      # Female (Gujarati - India, added)
    "ta": "ta-IN-PallaviNeural",     # Female (Tamil - India, added)
    "te": "te-IN-ShrutiNeural",      # Female (Telugu - India, added)
    "kn": "kn-IN-SapnaNeural",       # Female (Kannada - India, added)
    "ml": "ml-IN-SobhanaNeural",     # Female (Malayalam - India, added)
    "tr": "tr-TR-EmelNeural",        # Female (Turkish, added)
    "pl": "pl-PL-ZofiaNeural",       # Female (Polish, added)
    "nl": "nl-NL-FennaNeural",       # Female (Dutch - Netherlands, added)
    "sv": "sv-SE-SofieNeural",       # Female (Swedish - Sweden, added)
    "da": "da-DK-ChristelNeural",    # Female (Danish, added)
    "no": "no-NO-PernilleNeural",    # Female (Norwegian, added)
    "fi": "fi-FI-NooraNeural",       # Female (Finnish, added)
    "id": "id-ID-GadisNeural",       # Female (Indonesian, added)
    "th": "th-TH-PremwadeeNeural",   # Female (Thai, added)
    "vi": "vi-VN-HoaiMyNeural",      # Female (Vietnamese, added)
    # Fallback for any other language: English female
}


# Optimized buffer for faster playback
pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=256)
pygame.mixer.music.set_volume(1.0)

STOP_FLAG = threading.Event()

# =====================
# UNICODE HANDLING (FIX FOR BUG 5)
# =====================
def sanitize_unicode(text: str) -> str:
    """
    Only fix escaped sequences like \\u00e9.
    Do NOT re-encode already valid UTF-8 text.
    """
    if not text:
        return text

    try:
        # Only decode literal \uXXXX sequences
        if "\\u" in text:
            text = bytes(text, "utf-8").decode("unicode_escape")
    except Exception:
        pass

    return text

# language detection
def detect_language(text: str) -> str:
    try:
        clean = text.strip()

        # Force English for short system responses
        if len(clean) < 35:
            if re.fullmatch(r"[A-Za-z0-9\s.,!?':;%\-]+", clean):
                return "en"

        lang = detect(clean).lower()

        # If only basic Latin characters + common symbols → English
        if re.fullmatch(r"[A-Za-z0-9\s.,!?':;%\-]+", clean):
            return "en"

        return lang

    except LangDetectException:
        return "en"




# =====================
# TTS-friendly text preparation
# =====================
def prepare_text_for_tts(text: str) -> str:
    if not text:
        return text

    # First sanitize unicode
    text = sanitize_unicode(text)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)

    def number_to_ordinal(match):
        try:
            num = int(match.group(1))
            ordinals = {
                1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth",
                6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth"
            }
            return ordinals.get(num, f"{num}") + ", "
        except:
            return match.group(0)

    text = re.sub(r'(\d+)\.\s+', number_to_ordinal, text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-•*]\s+', 'Also, ', text, flags=re.MULTILINE)

    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =====================
# HELPERS
# =====================
def contains_hindi(text):
    return bool(re.search(r'[\u0900-\u097F]', text))

def contains_spanish(text):
    """Check if text contains Spanish characters"""
    spanish_chars = r'[áéíóúñü¿¡ÁÉÍÓÚÑÜ]'
    return bool(re.search(spanish_chars, text))

def clean_text(text):
    text = re.sub(r'https?://\S+', 'link', text)
    text = re.sub(r'www\.\S+', 'website', text)
    return text.strip()

def split_into_chunks(text: str, max_length: int = 600):
    """
    Split text into chunks for faster playback
    Split by sentences but keep chunks under max_length
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

# =====================
# OPTIMIZED STREAMING (FIX FOR BUG 4)
# =====================
async def tts_chunk_optimized(chunk: str, voice: str) -> BytesIO:
    """
    Compatible with very old edge-tts versions.
    Uses default MP3 stream.
    """
    communicate = edge_tts.Communicate(
        text=chunk,
        voice=voice,
        rate="+10%",
        pitch="+0Hz"
    )

    audio_buffer = BytesIO()

    async for data_chunk in communicate.stream():
        if isinstance(data_chunk, dict) and data_chunk.get("type") == "audio":
            audio_buffer.write(data_chunk.get("data"))

    audio_buffer.seek(0)
    return audio_buffer




async def stream_and_convert_optimized(text: str, voice: str, wav_queue: queue.Queue):
    """
    Stream with optimized chunking for faster initial playback
    """
    chunks = split_into_chunks(text, max_length=1000)
    
    for chunk in chunks:
        if STOP_FLAG.is_set():
            break
        try:
            wav_io = await tts_chunk_optimized(chunk, voice)
            wav_queue.put_nowait(wav_io)
        except Exception as e:
            print(f"TTS chunk error: {e}")
            # Continue with next chunk instead of stopping
            continue
    
    wav_queue.put_nowait(None)  # end signal

# =====================
# PLAYBACK THREAD (OPTIMIZED)
# =====================
def playback_thread_func(wav_queue: queue.Queue):
    """
    Optimized playback with minimal delays
    """
    while not STOP_FLAG.is_set():
        try:
            wav_io = wav_queue.get(timeout=0.1)
            if wav_io is None:
                break
            if isinstance(wav_io, BytesIO):
                try:
                    pygame.mixer.music.load(wav_io)
                    pygame.mixer.music.play()
                    # Reduced sleep time for faster responsiveness
                    while pygame.mixer.music.get_busy() and not STOP_FLAG.is_set():
                        time.sleep(0.005)
                except Exception as e:
                    print(f"Playback error: {e}")
                    continue
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Queue error: {e}")
            continue

# =====================
# TTSManager (OPTIMIZED)
# =====================
class TTSManager:
    def speak(self, text, func=None, check_interrupt=None):
        if not text or not text.strip():
            return None

        STOP_FLAG.clear()
        interrupt_query = None

        try:
            text = clean_text(text)
            speak_text = prepare_text_for_tts(text)
            
            # Detect language automatically
            lang = detect_language(speak_text)

            # Map language to voice
            voice = VOICE_MAP.get(lang, EN_VOICE)

            wav_queue = queue.Queue()

            # Synthesis in background
            loop = asyncio.new_event_loop()
            synth_thread = threading.Thread(
                target=lambda: loop.run_until_complete(
                    stream_and_convert_optimized(speak_text, voice, wav_queue)
                ),
                daemon=True
            )
            synth_thread.start()

            # Playback in separate thread
            play_thread = threading.Thread(
                target=playback_thread_func,
                args=(wav_queue,),
                daemon=True
            )
            play_thread.start()

            start = time.time()

            # Reduced sleep for faster loop/checks
            while synth_thread.is_alive() or play_thread.is_alive():
                if STOP_FLAG.is_set():
                    pygame.mixer.music.stop()
                    break

                if check_interrupt:
                    q = check_interrupt()
                    if q:
                        STOP_FLAG.set()
                        pygame.mixer.music.stop()
                        interrupt_query = q
                        print(f"🔇 Interrupted: {q}")
                        break

                if func and func() is False:
                    pygame.mixer.music.stop()
                    break

                time.sleep(0.005)  # Reduced from 0.02 for lower latency

                # Increased timeout for longer responses
                if time.time() - start > 45:
                    STOP_FLAG.set()
                    break

        except Exception as e:
            print(f"TTS error: {e}")

        finally:
            STOP_FLAG.set()
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except:
                pass

        time.sleep(0.01)  # Reduced final sleep from 0.05

        return interrupt_query

# Global TTS manager
tts_manager = TTSManager()

# =====================
# PUBLIC API
# =====================
def StopTTS():
    STOP_FLAG.set()
    try:
        pygame.mixer.music.stop()
    except:
        pass

def TextToSpeech(text, func=lambda: True, check_interrupt=None):
    return tts_manager.speak(text, func, check_interrupt)

def QuickSpeak(text):
    return tts_manager.speak(text, None, None)

# =====================
# TESTING
# =====================
if __name__ == "__main__":
    print("Testing OPTIMIZED TTS WITH UNICODE HANDLING...\n")

    test_phrases = [
        "こんにちは",
        "bonjour",
        "Volume set to 100%",
        "Hello! Testing optimized playback.",
        "Hola, ¿cómo estás? Esto es una prueba.",
        "Here are points: First point, Second point",
        "Testing unicode: café, naïve, résumé",
    ]

    for phrase in test_phrases:
        print(f"🔊 Testing: {phrase}")
        start = time.time()
        TextToSpeech(phrase)
        elapsed = time.time() - start
        print(f"⏱️ Total: {elapsed:.2f}s\n")
        time.sleep(0.3)

    print("✅ Test complete!")
