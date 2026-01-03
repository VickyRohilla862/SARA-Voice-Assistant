import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values

# Load environment variables from a .env file
env_vars = dotenv_values('.env')
AssistantVoice = env_vars.get("AssistantVoice")

# Ensure Data directory exists
os.makedirs('Data', exist_ok=True)

async def TextToAudioFile(text) -> None:
    """Convert text to an audio file asynchronously"""
    file_path = r'Data/Speech.mp3'
    if os.path.exists(file_path):
        os.remove(file_path)

    # Create the communicate object to generate speech
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(r'Data/Speech.mp3')

def TTS(Text, func=lambda r=None: True):
    """Manage text to speech functionality"""
    while True:
        try:
            # Convert text to an audio file asynchronously
            asyncio.run(TextToAudioFile(Text))
            # Initialize pygame mixer for audio playback
            pygame.mixer.init()
            # Load the generated speech file into pygame mixer
            pygame.mixer.music.load(r'Data/Speech.mp3')
            pygame.mixer.music.play()
            
            # Loop until the audio is done playing or the function stops
            while pygame.mixer.music.get_busy():
                if func() == False:
                    break
                pygame.time.Clock().tick(10)

            return True
        except Exception as e:
            print(f'Error in TTS: {e}')
            return False
        finally:
            try:
                # Call the provided function with False to signal the end of TTS
                func(False)
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
            except Exception as e:
                print(f'Error in Finally Block: {e}')

def TextToSpeech(Text, func=lambda r=None: True):
    """Manage text to speech with additional response for long text"""
    # List of predefined responses for cases where the text is too long
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]
    
    # For long text, speak only the first part and direct user to screen
    sentences = Text.split('.')
    if len(sentences) > 5:
        # Speak first few sentences
        short_text = '. '.join(sentences[:3]) + '.'
        TTS(short_text, func)
        # Add a response directing to screen
        TTS(random.choice(responses), func)
    else:
        # For shorter text, speak everything
        TTS(Text, func)
    
    return True

if __name__ == "__main__":
    while True:
        # Prompt user for input and pass it to TTS function
        TTS(input(">>> "))
