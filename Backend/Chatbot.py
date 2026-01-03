from groq import Groq # import the groq library to use AI service
from json import load, dump # import functions to read and write the json files
import datetime
from dotenv import dotenv_values

# load enviornment variables from the .env file
env_vars = dotenv_values('.env')
# retrieve specific enviornment variables for username, assistant name and API key

Username = env_vars.get('Username')
AssistantName = env_vars.get('AssistantName')
GroqAPIKey = env_vars.get('GroqAPIKey')

# initialize the groq client using the porvided API key
client = Groq(api_key = GroqAPIKey)

# initialize an empty list to store the message
messages = []

# define a system message that provides context to the AI chatbot about the role and behaviour
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

# a list of system instructions for the chatbot
SystemChatBot = [
    {'role':'system','content':System}
]

# attempt to load the chatlog from the JSON file
try:
    with open(r'Data/ChatLog.json', 'r') as f:
        message = load(f) # load existing message from chatlog

except FileNotFoundError:
    # if the file does not exist, create an empty json file
    with open(r'Data/ChatLog.json', 'w') as f:
        dump([], f)

# function to get realtime date and time
def RealtimeInformation():
    current_date_time = datetime.datetime.now() # get the current date and time
    day = current_date_time.strftime('%A') # day of the week
    date = current_date_time.strftime('%d') # date of the month
    month = current_date_time.strftime('%B') # full month name
    year = current_date_time.strftime('%Y') # year
    hour = current_date_time.strftime('%H') # hour
    minute = current_date_time.strftime('%M') # minute
    second = current_date_time.strftime('%S') # Second

    # format the information into a string
    data = f'Please use this real-time information if needed,\n'
    data += f'Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n'
    data += f'Time: {hour} Hours: {minute} Minutes: {second} Seconds\n'
    return data

# main chatbot function to handle user query
def ChatBot(Query):
    """This function sends the user's query to the chatbot and returns the AI response"""
    try:
        with open(r'Data/ChatLog.json', 'r') as f:
            messages = load(f)
        # append user's query to the message list
        messages.append({'role':'user','content':f'{Query}'})
        # make a request to the groq api for a response
        completion = client.chat.completions.create(
            model = 'llama-3.3-70b-versatile', # ai model to use
            messages = SystemChatBot+[{'role':'system','content':RealtimeInformation()}]+messages,# include system instructions, reaktime information and chat history
            max_tokens = 8192, # limit the max tokens in the response
            temperature = 0.7,
            top_p = 1, # use nucleus sampling to control diversity
            stream = True, # enable streaming response
            stop = None # allow the model to determine when to stop
        )

        Answer = "" # initialize an empty string to store the AI response

        # process the stream response chunks
        for chunk in completion:
            if chunk.choices[0].delta.content: #check if there is content in current chunk
                Answer += chunk.choices[0].delta.content # append the content to the answer

        Answer = Answer.replace("</s>", "") # clear any unwanted tokens from the response
        # append the chatbot's response to the message list
        messages.append({'role':'assistant','content': Answer})

        # save the updated chatlog to the json file
        with open(r'Data/ChatLog.json', 'w') as f:
            dump(messages, f, indent = 4)

        # return the response
        return Answer
        
    except Exception as e:
        # handle errors by printing the exception and resetting the chatlog
        print(f'Error: {e}')
        with open(r'Data/ChatLog.json', 'w') as f:
            dump([], f, indent = 4)

        return ChatBot(Query) # retry the query after resetting the log
    
# main entry point of the program
if __name__ == "__main__":
    while True:
        user_input = input(">>> ") # prompt the user for input
        print(ChatBot(user_input)) # call the chatbot function and print its response
