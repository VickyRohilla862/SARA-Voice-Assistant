import speech_recognition as sr
import mtranslate as mt
from dotenv import dotenv_values

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

    if any(q in text for q in question_words):
        return text.capitalize() + "?"
    else:
        return text.capitalize() + "."

def UniversalTranslator(text):
    translated = mt.translate(text, "en", "auto")
    return translated.capitalize()

def SpeechRecognition(timeout=5, phrase_limit=8):
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit
            )
        except sr.WaitTimeoutError:
            return None

    try:
        text = recognizer.recognize_google(audio, language=INPUT_LANG)
        print(f"🗣️ You said: {text}")

        if INPUT_LANG.lower().startswith("en"):
            return QueryModifier(text)
        else:
            return QueryModifier(UniversalTranslator(text))

    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        print("❌ Internet error")
        return None


if __name__ == "__main__":
    while True:
        result = SpeechRecognition()
        if result:
            print("✅ Final:", result)
        else:
            print("❌ Couldn't understand, try again\n")
