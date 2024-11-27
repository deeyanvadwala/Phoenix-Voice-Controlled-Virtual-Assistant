#Libraries
import speech_recognition as sr 
import pyttsx3
import time
import datetime
import openai
import webbrowser
import subprocess
from Greetings import greeting
from Search import*
import requests
from bs4 import BeautifulSoup
import os
import pywhatkit
from vol import volumeup,volumedown
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# Define the prompt template for LangChain
template = """
Answer the following question

Here's the conversation history: {context}

Question: {question}

Answer:
"""

# Initialize the LLaMA 3 model using LangChain's Ollama integration
model = OllamaLLM(model='llama3')
prompts = ChatPromptTemplate.from_template(template)
chain = prompts | model


#variables
listener = sr.Recognizer() 
strTime=datetime.datetime.now().strftime("%H:%M")

#Functions

def wake_word():
    listener = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening")
        voice = listener.listen(source)
        try:
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'phoenix' in command:
                greeting()
                #Speak("Hi Deeyan, My Name Is Phoenix I Am Your Virtual Assistant, How Can I Help You Today")
                while 1:
                    if not Listen():
                        break
            else:
                wake_word()
        except:
            wake_word()

def sleep():
     listener = sr.Recognizer()
     with sr.Microphone() as source:
         print("Listening")
         voice = listener.listen(source)
         try:
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'phoenix' in command:
                Speak("Hi Deeyan, How Can I Help You Today")
                Listen()
            else:
                sleep()
         except:
            sleep()

def Speak(text):
    rate= 100
    engine = pyttsx3.init() 
    voices = engine.getProperty('voices') 
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', rate+50)
    engine.say(text)
    engine.runAndWait()


def Listen():
    listener = sr.Recognizer()
    with sr.Microphone() as source:
        Speak("Listening")
        voice = listener.listen(source)
        try:
            command = listener.recognize_google(voice)
            command = command.lower()
            
            if 'how are you' in command:
                Speak("I'm Fine Thank You")
            elif 'i am fine' in command:
                Speak("That's Great How Can I Help You Today?")
            elif 'thank you' in command:
                Speak("You are Welcome,Sir")
            elif 'time' in command:
                Speak(f"The Time Is {strTime}")
            elif 'open google' in command:
                Speak("Opening Google")
                webbrowser.open_new('https://www.google.com/')
            elif 'open chatgpt' in command:
                Speak("Opening ChatGpt")
                webbrowser.open_new('https://chatgpt.com/')
            elif 'open youtube' in command:
                Speak("Opening YouTube")
                webbrowser.open_new('https://www.youtube.com/')
            elif 'open my mail' in command:
                Speak("Opening Your Mail")
                webbrowser.open_new('https://mail.google.com/mail/u/1/#inbox')
            elif 'open calculator' in command:
                Speak("Opening Calculator")
                subprocess.Popen(r'C:\Windows\System32\calc.exe')
            elif 'open notepad' in command:
                Speak("Opening Notepad")
                subprocess.Popen(r'C:\Windows\System32\notepad.exe')
            elif 'open command prompt' in command:
                Speak("Opening CMD")
                subprocess.Popen(r'C:\Windows\System32\cmd.exe')    
            elif 'open source file' in command:
                Speak("Opening Source File")
                subprocess.Popen(r'explorer.exe D:\Laptop\Phoneix')
            elif 'google' in command:
                searchGoogle(command)
            elif 'youtube' in command:
                searchYoutube(command)
            elif 'weather' in command: 
                search = "weather in ahmedabad"
                url = f"https://www.google.com/search?client=firefox-b-d&q={search}"
                r = requests.get(url)
                data = BeautifulSoup(r.text,"html.parser")
                weath = data.find("div", class_ = "BNeawe").text
                Speak(f"current{search} is {weath}")
            elif "volume up" in command:
                    Speak("Turning volume up,sir")
                    volumeup()
            elif "volume down" in command:
                Speak("Turning volume down, sir")
                volumedown()
            elif 'sleep' in command:
                Speak("Going To Sleep")
                sleep()
            elif 'terminate' in command:
                Speak("Shutting Down")
                return 0
            else:
                result = chain.invoke({'context': '', 'question': command})
                Speak(result)
        except:
            Speak("Sorry, I Didn't Get That")
    return 1

#Main Function
wake_word()
