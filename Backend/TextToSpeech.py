import pygame # import pygame library to handle audio playback
import random # import random for generating random choices
import asyncio # import asyncio for asynchronous operations
import edge_tts # to handle text to speech functionality
import os
from dotenv import dotenv_values

# load enviornment variables from a .env file
env_vars = dotenv_values('.env')
AssistantVoice = env_vars.get("AssistantVoice") # get the assistant voice

# asynchronous function to convert text to an audio file
async def TextToAudioFile(text) -> None:
    file_path = r'Data/Speech.mp3' # define the file path to save the audio file
    if os.path.exists(file_path): # check if file path exists already
        os.remove(file_path) # if it exists, remove it to avoid overwriting errors

    # create the communicate object to generate speech
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch = '+5Hz', rate = '+13%')
    await communicate.save(r'Data/Speech.mp3')

# function to manage text to speech functionality
def TTS(Text, func = lambda r = None:True):
    while True:
        try:
            #convert text to an audio file asynchronously
            asyncio.run(TextToAudioFile(Text))
            #initialize pygame mixer for audio playback
            pygame.mixer.init()
            # load the generated speech file into pygame mixer
            pygame.mixer.music.load(r'Data/Speech.mp3')
            pygame.mixer.music.play() # play the audio
            # loop until the audio is done playing or the function stops
            while pygame.mixer.music.get_busy():
                if func() == False: # check if the external function return false
                    break
                pygame.time.Clock().tick(10) # limit the loop to 10 ticks per second

            return True # return true if the audio file played successfully
        except Exception as e:
            print(f'Error in TTS: {e}')

        finally:
            try:
                # call the provided function with false to signal the end of TTS
                func(False)
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop() # stop the audio playback 
                    pygame.mixer.quit() # quit the pygame mixer

            except Exception as e:
                print(f'Error in Finally Block: {e}')

# function to manage text to speech with additional response for long text
def TextToSpeech(Text, func = lambda r = None:True):
    Data = str(Text.split('.')) # split the text by period into a list of sentences
    #list of predefined responses for case where the text is too long
    responses = []
    TTS(Text, func)

# main entry point for the program
if __name__ == "__main__":
    while True:
        # prompt user for input and pass it to TextToSpeech function
        TTS(input(">>> "))