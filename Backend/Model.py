import cohere # import the cohere library for AI services
from rich import print # import the rich library to enhance terminal output
from dotenv import dotenv_values # import dotenv to load enviornment variables from .env file

# load enviornment variables
env_vars = dotenv_values('.env')
#retrieve API key
CohereAPIKey = env_vars.get('CohereAPIKey')

# create a cohere client using the provided API key
co = cohere.Client(api_key=CohereAPIKey)

# define a list of recognisedfunction keywords for task categorization
funcs = ['exit', 'general', 'realtime', 'open', 'close', 'play', 'generate image', 'system', 'content', 'google search', 'youtube search', 'reminder']

# initialize an empty list to store user messages
messages = []

# define the preamble that guides the AI model on how to categorize queries
preamble = """"""

#define a chat histore with predefined user-chatbot interaction for context
ChatHistory = [
    {'role':'user','message':'how are you'},
    {'role':'chatbot','message':'general how are you'},
    {'role':'user','message':'do you like pizza?'},
    {'role':'chatbot','message':'general do you like pizza?'},
    {'role':'user','message':'open chrome and tell me about mahatama gandhi'},
    {'role':'chatbot','message':'open chrome, general tell me about mahatama gandhi'},
    {'role':'user','message':'open chrome and firefox'},
    {'role':'chatbot','message':'open chrome, open firefox'},
    {'role':'user','message':'whats todays date and by the way remind me that i have dancing perfromance on 5th aug at 11pm'},
    {'role':'chatbot','message':'general whats todays date, reminder 11:00pm 5th aug dancing performance'},
    {'role':'user','message':'chat with me'},
    {'role':'chatbot','message':'general chat with me'}
]

# define the main function for decision making on queries
def FirstLayerDMM(prompt:str = 'test'):
    #add the user's query to the message list
    messages.append({'role':'user','content':f'{prompt}'})
    #create a streaming chat session with the cohere model
    stream = co.chat_stream(
        model = 'command-r-plus-08-2024', # specify the cohere model
        message = prompt, # pass the user's query
        temperature = 0.7, # set the creativity level of the model
        chat_history = ChatHistory, # provide the predefined chat histor
        prompt_truncation = 'OFF', # ensure the prompt is not truncated
        connectors = [], # no additional connectors are used
        preamble = preamble # pass the detailed intruction preamble
    )

    # initialize an empty string to store the generated response
    response = ""
    # iterates over events in the stream and capture text generation events
    for event in stream:
        if event.event_type == 'text-generation':
            response += event.text # append generated text to the response

    # remove new line characters and split responses into individual tasks
    response = response.replace('\n', '')
    response = response.split(',')

    # strip leading and trailing white spaces from each task
    response = [i.strip() for i in response]

    #initialize an empty list to filter valid tasks
    temp = []

    # filter the tasks based on recognized function keywords
    for task in response:
        for func in funcs:
            if task.startswith(func):
                temp.append(task) # add valid task to filtered list

    # update the response with the filtered list of tasks
    response = temp

    # if '(query)' is in the response, recursively call the function for further clarification
    if '(query)' in response:
        newresponse = FirstLayerDMM(prompt = prompt)
        return newresponse # return the clarified response
    
    else:
        return response # return the filtered response
    
# entry point for the script
if __name__ == "__main__":
    # continuously prompt the user for input and process it
    while True:
        print(FirstLayerDMM(input(">>> "))) # print the categorized response