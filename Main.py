from Frontend.GUI import GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen, TempDirPath, SetMicrophoneStatus, QueryModifier, GetMicrophoneStatus, GetAssistantStatus
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
env_vars = dotenv_values('.env')
Username = env_vars.get('Username')
AssistantName = env_vars.get('AssistantName')
DefaultMessage = f'''{Username}: Hello {AssistantName}, How are you?
{AssistantName}: Welcome {Username}. I am doing well. How may I help you? Do you need anything to know about Environment? Whatever it is. I am always here to help you.'''
subprocess = []
Functions = ['open', 'close', 'play', 'system', 'content', 'google search', 'youtube search']

def ShowDefaultChatIfNoChats():
    File = open(r'Data/ChatLog.json', 'r', encoding = 'utf-8')
    if len(File.read())<5:
        with open(rf'{TempDirPath}/Database.data', 'w', encoding = 'utf-8') as file:
            file.write("")

        with open(rf'{TempDirPath}/Responses.data', 'w', encoding = 'utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r'Data/ChatLog.json', 'r', encoding = 'utf-8') as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry['role'] == 'user':
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry['role'] == 'assistant':
            formatted_chatlog += f"Assistant: {entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace('User', Username+" ")
    formatted_chatlog = formatted_chatlog.replace('Assistant', AssistantName+" ")
    with open(rf'{TempDirPath}/Database.data', 'w', encoding = 'utf-8') as file:
        file.write(formatted_chatlog) 

def ShowChatsOnGUI():
    File = open(rf'{TempDirPath}/Database.data', 'r', encoding = 'utf-8')
    Data = File.read()
    if len(str(Data)) > 0:
        lines = Data.split('\n')
        results = '\n'.join(lines)
        File.close()
        File = open(rf'{TempDirPath}/Responses.data', 'w', encoding = 'utf-8')
        File.write(results)
        File.close()

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()
    ShowTextToScreen(f'{Username}: {Query}')
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)
    print("")
    print(f'Decision: {Decision}')
    print("")
    G = any([i for i in Decision if i.startswith('general')])
    R = any([i for i in Decision if i.startswith('realtime')])
    Merged_Query = " and ".join([" ".join(i.split()[1:]) for i in Decision if i.startswith('general') or i.startswith('realtime')])
    for queries in Decision:
        if 'generate' in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution =True

    for queries in Decision:
        if TaskExecution == False:
            if any(queries.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution == True:
        with open(r'Frontend/Files/ImageGeneration.data', 'w') as file:
            file.write(f'{ImageGenerationQuery},True')

        try:
            p1 = subprocess.Popen(['python', r'Backend/ImageGeneration.py'], stdout = subprocess.PIPE, stderr = subprocess.PIPE, stdin = subprocess.PIPE, shell = False)
            subprocess.append(p1)
        except Exception as e:
            print(f'Error Starting ImageGeneration.py: {e}')
    
    if G and R:
        SetAssistantStatus('Searching...')
        Answer = RealtimeSearchEngine(QueryModifier(Merged_Query))
        ShowTextToScreen([f"{AssistantName}: {Answer}"])
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
    
    else:
        for queries in Decision:
            if 'general' in queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = queries.replace('general ', '')
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f'{AssistantName}: {Answer}')
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            
            elif 'realtime' in queries:
                SetAssistantStatus("Searching...")
                QueryFinal = queries.replace('realtime ', '')
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f'{AssistantName}: {Answer}')
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            
            elif 'exit' in queries:
                QueryFinal = f'Okay Bye {Username}. I will be here if you need help in anything. Especially in topics related to environment'
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f'{AssistantName}: {Answer}')
                TextToSpeech(Answer)
                SetAssistantStatus("Answering...")
                os._exit(1)

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        if CurrentStatus == 'True':
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            if 'Available...' in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus('Available...')

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    thread2 = threading.Thread(target = FirstThread, daemon = True)
    thread2.start()
    SecondThread()