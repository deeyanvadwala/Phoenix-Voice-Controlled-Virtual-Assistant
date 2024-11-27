import pyttsx3
import datetime
def Speak(text):
    rate= 100
    engine = pyttsx3.init() 
    voices = engine.getProperty('voices') 
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', rate+50)
    engine.say(text)
    engine.runAndWait()

def greeting():
    hour=int(datetime.datetime.now().hour)
    if hour>=0 and hour<=12:
        Speak("Good Morning,Deeyan")
    elif hour>=12 and hour<=18:
        Speak("Good Afternoon,Deeyan")
    else:
        Speak("Good Evening,Deeyan")
    Speak("My Name Is Phoenix I Am Your Virtual Assistant, How Are You?")

"""
For Multiple greeting options 
greetings_reply=["Greetings sir , How can i help you?", "Hi, how can I assist you?", "Nice to see you!","Hey, what can I do for you?","Hi, I'm here to help!",
    "Hey, ready for some chat?","Hi, what's on your mind?","Hey, how can I make your day better?", "Hello! What can I do for you today?","Hello, how can I be of service today?",
    "Hi, ready to dive into a chat?","Hey! Welcome to Jarvis. How can I help you today?","My Name Is Jarvis I Am Your Virtual Assistant, How Are You?"]

greetings_var =  random.choice(greetings_reply)
Speak(greetings_var)
"""