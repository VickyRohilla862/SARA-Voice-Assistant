import speech_recognition as sr
import mtranslate as mt
from dotenv import dotenv_values
from Frontend.GUI import SetAssistantStatus
import time

# Load env
env = dotenv_values(".env")
INPUT_LANG = env.get("InputLanguage", "en-IN")

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True


def QueryModifier(text):
    text = text.strip().lower()
    if not text:
        return None

    question_words = (
        "how", "what", "who", "where", "when",
        "why", "which", "can you", "what's", "where's"
    )

    if any(text.startswith(q) for q in question_words):
        return text.capitalize() + "?"
    else:
        return text.capitalize() + "."


def UniversalTranslator(text):
    translated = mt.translate(text, "en", "auto")
    return translated.capitalize()


def SpeechRecognition(timeout=5, phrase_limit=8):
    SetAssistantStatus("🎤 Listening...")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit
            )
        except sr.WaitTimeoutError:
            SetAssistantStatus("❌ No speech detected")
            time.sleep(1)
            return None

    SetAssistantStatus("⏳ Processing...")

    try:
        text = recognizer.recognize_google(audio, language=INPUT_LANG)
        SetAssistantStatus(f"🗣️ Heard: {text}")

        if INPUT_LANG.lower().startswith("en"):
            return QueryModifier(text)
        else:
            return QueryModifier(UniversalTranslator(text))

    except sr.UnknownValueError:
        SetAssistantStatus("❌ Couldn't understand")
        time.sleep(1)
        return None

    except sr.RequestError:
        SetAssistantStatus("🌐 Internet error")
        time.sleep(1)
        return None
