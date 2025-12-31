from AppOpener import open as appopen # import functions to open and close apps
from webbrowser import open # import webbrowser functionality
from pywhatkit import search, playonyt # import functions for google search and youtube playback
from dotenv import dotenv_values
from bs4 import BeautifulSoup # import BeautifulSoup for parsing HTML content
from rich import print
from groq import Groq
import webbrowser
import re
import subprocess # import subprocess for interaction with the system
import keyboard
import psutil # provides an easy way to retrieve information about system utilization
import asyncio
import os
from ctypes import POINTER, cast #used to call C functions and use C-compatible data types directly from Python without writing a Python C extension
from comtypes import CLSCTX_ALL #  for working with COM (Component Object Model) objects on Windows
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# load enviornment variables from .env file
env_vars = dotenv_values('.env')
GroqAPIKey = env_vars.get('GroqAPIKey')

# define css classes for prasing specific element in html content
classes = ['zCubwf','hgkElc','LTKOO sY7ric','Z0LcW','gsrt vk_bk FzvWSb YwPhnf','pclqee','tw-Data-text tw-text-small tw-ta','IZ6rdc','O5uR6d LTKOO','vlzY6d','webanswers_webanswers_table__webanswers_table','dDoNo ikd4Bb gsrt','sXLaOe','LWkfKe','VQF4g','qv3Wpe','kno-rdesc','SPZz6b']

# define a user-agent for making web requests
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; X64) AppleWeKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

# initialize the groq client with the api key
client = Groq(api_key = GroqAPIKey)

# predefined professional responses for user interactions
professional_responses = {
    "Your satisfaction is my priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask."
}

# list to store chatbot messages
messages = []

# system message to provide context to the chatbot
SystemChatBot = [
    {'role':'system','content':f"Hello, I'm {os.environ['Username']}, You're a content writer. You have to write content like letters, codes, application, essays, notes, songs, poems etc."}
]

# function to perform a google search
def GoogleSearch(Topic):
    search(Topic) # use pywhatkit's search function
    return True # indicate success

# function to generate content using AI and save it to a file
def Content(Topic):
    # function to generate content using AI and save it to file in Notepad
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe' # default text editor
        subprocess.Popen([default_text_editor, File]) # open the file in notepad

    # nested function to generate content using the AI chatbot
    def ContentWriterAI(prompt):
        messages.append({'role':'user','content':f'{prompt}'})
        completion = client.chat.completions.create(
            model = 'llama-3.3-70b-versatile', #specify the AI model
            messages = SystemChatBot+messages,
            max_tokens = 8192,
            temperature = 0.7,
            top_p = 1,
            stream = True,
            stop = None
        )
        Answer = "" # initialize an empty string for the response
        # process streamed resposne chunks
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        Answer = Answer.replace('</s>',"")
        messages.append({'role':'assistant','content':Answer})
        return Answer
    # Topic: str = Topic.replace('Content ', "") # remove 'Content ' from the topic
    ContentByAI = ContentWriterAI(Topic) # generate content using AI
    # save the generated content to a text file
    with open(rf"Data/{Topic.lower().replace(' ', '')}.txt", 'w', encoding = 'utf-8') as file:
        file.write(ContentByAI) # write the content to the file
        file.close()
    
    OpenNotepad(rf"Data/{Topic.lower().replace(' ', '')}.txt")
    return True

# function to search for a topic on youtube
def YoutubeSearh(Topic):
    Url4Search = f"https:www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

# function to play a video on youtube
def PlayYoutube(query):
    playonyt(query)
    return True

#function to open an application or a rellevant webpage

def OpenApp(app):
    app = app.strip().lower()

    # If full URL
    if re.match(r'^https?://', app):
        webbrowser.open(app)
        return True

    # Try desktop application
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        pass

    # MAGIC: DuckDuckGo !ducky → opens FIRST website directly
    webbrowser.open(f"https://duckduckgo.com/?q=!ducky+{app}")
    return True


# function to close an application

def CloseApp(app_name: str):
    """
    Force close an app by searching for and killing matching processes.
    Uses psutil for reliable process detection and killing.
    """
    app_name = app_name.lower().strip()
    if not app_name:
        return False
    
    # Take the last word as the key (e.g., 'google chrome' -> 'chrome')
    # This handles apps with spaces better (e.g., matches 'chrome.exe' for 'chrome')
    key = app_name.split()[-1] if app_name.split() else app_name
    
    killed = False
    for proc in psutil.process_iter(['pid', 'name']):
        proc_name = proc.info['name'].lower() if proc.info['name'] else ''
        if key in proc_name:  # Substring match (flexible)
            try:
                proc.kill()  # Force kill (like taskkill /f)
                print(f"Killed process: {proc.info['name']} (PID: {proc.info['pid']})")  # Debug log
                killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"Failed to kill {proc.info['name']}: {e}")  # Debug log
                pass
    if not killed:
        print(f"No matching processes found for '{app_name}' (key: '{key}')")  # Debug log
    return killed

        
def set_volume(level: int):
    level = max(0, min(level, 100))  # clamp 0–100

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None
    )
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    volume.SetMasterVolumeLevelScalar(level / 100, None)
        
# function to execute system level commands
def System(command):
    command = command.strip()

    def press(key, times):
        for _ in range(times):
            keyboard.press_and_release(key)

    if command == 'mute':
        keyboard.press_and_release('volume mute')

    elif command == 'unmute':
        keyboard.press_and_release('volume mute')

    elif command == 'volume up':
        keyboard.press_and_release('volume up')

    elif command == 'volume down':
        keyboard.press_and_release('volume down')

    elif command.startswith('set volume '):
        level = int(command.replace('set volume ', '').strip())
        level = max(0, min(level, 100))

        # 🔥 TRUE RESET METHOD
        press('volume down', 50)     # force to ~0
        press('volume up', level // 2)

    elif command.startswith('increase volume '):
        amount = int(command.replace('increase volume ', '').strip())
        press('volume up', amount // 2)

    elif command.startswith('decrease volume '):
        amount = int(command.replace('decrease volume ', '').strip())
        press('volume down', amount // 2)

    return True


# asynchronous function to translate and execute user commands
async def TranslateAndExecute(commands:list[str]):
    funcs = [] # list to store asynchronous tasks

    for command in commands:
        command = command.lower().strip()

        # 🔊 SET VOLUME
        if re.search(r'(set|turn).*volume.*\d+', command):
            level = re.search(r'(\d{1,3})', command).group()
            command = f"system set volume {level}"

        # 🔼 INCREASE VOLUME
        elif re.search(r'(increase|raise).*volume.*\d+', command):
            amount = re.search(r'(\d{1,3})', command).group()
            command = f"system increase volume {amount}"

        # 🔽 DECREASE VOLUME  ✅ FIXED
        elif re.search(r'(decrease|lower).*volume.*\d+', command):
            amount = re.search(r'(\d{1,3})', command).group()
            command = f"system decrease volume {amount}"

        elif 'mute' in command:
            command = 'system mute'

        elif 'unmute' in command:
            command = 'system unmute'


        elif command.startswith(('write', 'create', 'generate', 'compose')):
            command = 'content ' + command



        if command.startswith('open '): # handle open commands
            if 'open it' in command: # ignore open it commands
                pass
            if 'open file' in command: # ignore open file command
                pass
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix('open ')) # schedule app opening
                funcs.append(fun)
        elif command.startswith('general '): # place holder for general commands
            pass
        elif command.startswith('realtime '): # place holder for realtime commands
            pass
        elif command.startswith('close '): # handle close commands
            fun = asyncio.to_thread(CloseApp, command.removeprefix('close ')) # schedule app closing
            funcs.append(fun)
        elif command.startswith('play '): # handle play commands
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix('paly '))
            funcs.append(fun)
        elif command.startswith('content '): # handle content command
            fun = asyncio.to_thread(Content, command.removeprefix('content '))
            funcs.append(fun)
        elif command.startswith('google search '): # handle google search commands
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix('google search '))
            funcs.append(fun)
        elif command.startswith('youtube search '): # handle youtube search commands
            fun = asyncio.to_thread(YoutubeSearh, command.removeprefix('youtube search '))
            funcs.append(fun)
        elif command.startswith('system '): # handle system command
            fun = asyncio.to_thread(System, command.removeprefix('system '))
            funcs.append(fun)
        else:
            print(f'No function found for {command}') # print the error for unrecognized commands
    
    results = await asyncio.gather(*funcs) # execute all tasks concurrently
    for result in results: # process the result
        if isinstance(result, str):
            yield result
        else:
            yield result

# asynchronous function to automate command execution
async def Automation(command:list[str]):
    async for result in TranslateAndExecute(command):
        pass
    return True # indicates success

# main entry point of the program
if __name__ == '__main__':
    asyncio.run(Automation(['close taskmgr']))