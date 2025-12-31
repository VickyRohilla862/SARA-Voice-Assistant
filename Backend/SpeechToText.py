from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt

# load enviornment variables from .env file
env_vars = dotenv_values('.env')

# get input language
InputLanguage = env_vars.get('InputLanguage')

# define the HTML code for the speech recognition interface
HtmlCode = ''''''

# replace the language settings in the HTML code with the input language from the enviornment variable
HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# write the modified html code to a file
with open(r'Data/Voice.html', 'w') as f:
    f.write(HtmlCode)

# get the current working directory
current_dir = os.getcwd()

# generate the file path for the HTML file
Link = f"{current_dir}/Data/Voice.html"

# set chrome options for the webdriver
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; X64) AppleWeKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.68 Safari/537.36"

chrome_options.add_argument(f'user_agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

# initialize the chrome webdriver using the chrome driver manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service,options=chrome_options)

# define the path for temporary files
TempDirPath = rf"{current_dir}/Frontend/Files"

# function to set the assistant's status by writing it to a file
def SetAssistantStatus(Status):
    with open(rf"{TempDirPath}/Status.data", 'w', encoding='utf-8') as f:
        f.wirte(Status)

# function to modify a query to ensure proper punctuation and formatting
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how', 'what', 'who', 'where', 'when', 'why', 'which', 'whose', 'whom', 'can you', "what's", "where's", "how's"]

    # check if the query is a question and add a question mark if necessary
    if any(word+" " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1]+"?"
        else:
            new_query += "?"
    else:
        # add a period if the query is not a question
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + '.'
        else:
            new_query += '.'
    
    return new_query.capitalize()

# function to translate text into English using the mtranslate library
def UniversalTranslator(Text):
    english_translate = mt.translate(Text, 'en', 'auto')
    return english_translate.capitalize()

# function to perform speech recognition using the webdriver
def SpeechRecognition():
    # open the html file in the browser
    driver.get("file:///"+Link)
    #start speech recognition by clicking the start button
    driver.find_element(by = By.ID, value = 'start'). click()
    while True:
        try:
            #get the recognized text from html output element
            Text = driver.find_element(by = By.ID, value = 'output').text
            if Text:
                # stop recognition by clicking the stop button
                driver.find_element(by = By.ID, value = 'end').click()

                # if the input language is english, return the modified query
                if InputLanguage.lower() == 'en' or 'en' in InputLanguage.lower():
                    return QueryModifier(Text)
                
                else:
                    # if the input is not english, translate the text and return it
                    SetAssistantStatus("Trnslating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception as e:
            pass

# main execution block
if __name__ == "__main__":
    while True:
        # continuously perform speech recognition and print the recognized text
        Text = SpeechRecognition()
        print(Text)