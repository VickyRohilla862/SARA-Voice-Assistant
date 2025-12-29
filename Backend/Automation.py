from AppOpener import close, open as appopen # import functions to open and close apps
from webbrowser import open as webopen # import webbrowser functionality
from pywhatkit import search, playonyt # import functions for google search and youtube playback
from dotenv import dotenv_values
from bs4 import BeautifulSoup # import BeautifulSoup for parsing HTML content
from rich import print
from groq import Groq
import webbrowser
import subprocess # import subprocess for interaction with the system
import requests # import requests to make http request
import keyboard
import asyncio
import os

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
            model = 'maxtral-8x7b-32768', #specify the AI model
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
        messages.apppend({'role':'assistant','content':Answer})
        return Answer
    Topic: str = Topic.replace('Content ', "") # remove 'Content ' from the topic
    ContentByAI = ContentWriterAI(Topic) # generate content using AI
    # save the generated content to a text file
    with open(rf"Data/{Topic.lower().replace(' ', '')}.txt", 'w', encoding = 'utf-8') as file:
        file.write(ContentByAI) # write the content to the file
        file.close()
    
    OpenNotepad(rf"Data/{Topic.lower().replace(" ", "")}.txt")
    return True
