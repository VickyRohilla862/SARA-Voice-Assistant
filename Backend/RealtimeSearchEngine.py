from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

# load enviornment variables for .env file
env_vars = dotenv_values('.env')
# retrieve enviornment variables for the chatbot configuration
Username = env_vars.get('Username')
AssistantName = env_vars.get('AssistantName')
GroqAPIKey = env_vars.get('GroqAPIKey')

# initialize the groq client with the API key
client = Groq(api_key = GroqAPIKey)

# define the system instructions for the chatbot
System = """"""

# try to load the chatlog from the json file or create a new one if it doesnt exist
try:
    with open(r'Data/ChatLog.json', 'r') as f:
        messages = load(f)

except:
    with open(r'Data/ChatLog.json', 'w') as f:
        dump([], f)

# function to perform google search and format the results
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=10))
    Answer = f'The search results for "{query}" are:\n[start]\n'
    for i in results:
        Answer += f'Title: {i.title}\nDescription: {i.description}\n\n'
    Answer += "[end]"
    return Answer

# pre defined chatbot conversation system message and an initial user message
SystemChatBot = [
    {'role':'system','content':System},
    {'role':'user','content':'hi'},
    {'role':'assistant','content':'Hello, how can i help you?'}
]

# function to get the realtime information like current date and time
def Information():
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

# function to handle realtime search and response generation

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    # load the chatlog from the json file
    with open(r'Data/ChatLog.json', 'r') as f:
        messages = load(f)
        messages.append({'role':'user','content':f'prompt'})

    # add google search results to the system chatbot messages
    SystemChatBot.append({'role':'system','content':GoogleSearch(prompt)})

    # generate a response using the groq client 
    completion = client.chat.completions.create(
        model = 'llama-3.3-70b-versatile',
        messages = SystemChatBot+[{'role':'system','content':Information()}]+messages,
        temperature = 0.7,
        max_tokens = 8192,
        top_p = 1,
        stream = True,
        stop = None
    )

    Answer = ""

    # concationate response chunks from the streaming output
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    # clean up the response
    Answer = Answer.strip().replace('</s>', '')
    messages.append({'role':'assistant','content':Answer})

    # save the updated chatlog back to the json file
    with open(r'Data/ChatLog.json', 'w') as f:
        dump(messages, f, indent = 4)

    # remove the most recent system from the chatbot conversation
    SystemChatBot.pop()
    return Answer

# main entry point for the program
if __name__ == '__main__':
    while True:
        prompt = input(">>> ")
        print(RealtimeSearchEngine(prompt))