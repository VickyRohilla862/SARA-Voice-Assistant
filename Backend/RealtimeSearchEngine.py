from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os

# Load environment variables from .env file
env_vars = dotenv_values('.env')

# Retrieve environment variables for the chatbot configuration
Username = env_vars.get('Username')
AssistantName = env_vars.get('AssistantName')
GroqAPIKey = env_vars.get('GroqAPIKey')

# Initialize the Groq client with the API key
client = Groq(api_key=GroqAPIKey)

# Define the system instructions for the chatbot
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Ensure Data directory exists
os.makedirs('Data', exist_ok=True)

# Try to load the chatlog from the JSON file or create a new one if it doesn't exist
try:
    with open(r'Data/ChatLog.json', 'r') as f:
        messages = load(f)
except FileNotFoundError:
    with open(r'Data/ChatLog.json', 'w') as f:
        dump([], f)
    messages = []

def GoogleSearch(query):
    """Perform Google search and format the results"""
    results = list(search(query, advanced=True, num_results=10))
    Answer = f'The search results for "{query}" are:\n[start]\n'
    for i in results:
        Answer += f'Title: {i.title}\nDescription: {i.description}\n\n'
    Answer += "[end]"
    return Answer

# Predefined chatbot conversation system message and an initial user message
SystemChatBot = [
    {'role': 'system', 'content': System},
    {'role': 'user', 'content': 'hi'},
    {'role': 'assistant', 'content': 'Hello, how can I help you?'}
]

def Information():
    """Get the realtime information like current date and time"""
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime('%A')
    date = current_date_time.strftime('%d')
    month = current_date_time.strftime('%B')
    year = current_date_time.strftime('%Y')
    hour = current_date_time.strftime('%H')
    minute = current_date_time.strftime('%M')
    second = current_date_time.strftime('%S')
    data += f'Use this realtime information if needed:\n'
    data += f'Day: {day}\n'
    data += f'Date: {date}\n'
    data += f'Month: {month}\n'
    data += f'Year: {year}\n'
    data += f'Time: {hour} Hours: {minute} Minutes: {second} Seconds.\n'
    return data

def RealtimeSearchEngine(prompt):
    """Handle realtime search and response generation"""
    global SystemChatBot, messages

    # Load the chatlog from the JSON file
    with open(r'Data/ChatLog.json', 'r') as f:
        messages = load(f)
        messages.append({'role': 'user', 'content': f'{prompt}'})

    # Add Google search results to the system chatbot messages
    SystemChatBot.append({'role': 'system', 'content': GoogleSearch(prompt)})

    # Generate a response using the Groq client
    completion = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=SystemChatBot + [{'role': 'system', 'content': Information()}] + messages,
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""

    # Concatenate response chunks from the streaming output
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    # Clean up the response
    Answer = Answer.strip().replace('</s>', '')
    messages.append({'role': 'assistant', 'content': Answer})

    # Save the updated chatlog back to the JSON file
    with open(r'Data/ChatLog.json', 'w') as f:
        dump(messages, f, indent=4)

    # Remove the most recent system message from the chatbot conversation
    SystemChatBot.pop()
    return Answer

if __name__ == '__main__':
    while True:
        prompt = input(">>> ")
        print(RealtimeSearchEngine(prompt))
