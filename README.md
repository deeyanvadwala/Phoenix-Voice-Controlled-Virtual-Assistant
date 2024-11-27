# Phoenix-Voice-Controlled-Virtual-Assistant
Phoenix is a Python-based voice-controlled virtual assistant that can perform tasks like web browsing, interacting with APIs, answering questions via LLaMA 3 model integration, and controlling system operations.

## Features  
- **Voice Commands**: Perform tasks like opening applications, web browsing, and checking the time with simple voice commands.  
- **LangChain Integration**: Leverages the LLaMA 3 model for advanced question answering and contextual responses.  
- **Web Scraping**: Fetches weather updates using `requests` and `BeautifulSoup`.  
- **System Utilities**: Includes volume control, calculator, notepad, and command prompt access.  
- **Modular Design**: Cleanly organized functions for scalability and ease of maintenance.  

## Technologies Used  
- **Python Libraries**: `speech_recognition`, `pyttsx3`, `requests`, `BeautifulSoup`, `pywhatkit`, `subprocess`.  
- **AI Integration**: LangChain's Ollama LLM for intelligent conversation capabilities.  

## Prerequisites  
- Python 3.8 or above.  
- Internet connection for web-based functionalities.  

## How to Run  
1. Clone the repository:  
   ```bash
   git clone https://github.com/<your-username>/phoenix-virtual-assistant.git
   cd phoenix-virtual-assistant

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
3. Run the assistant: 
   ```bash
   python phoenix.py


## Key Functionalities  
- **Voice Recognition**: Uses `speech_recognition` to listen and process user commands seamlessly.  
- **Speech Synthesis**: Utilizes `pyttsx3` to convert text to speech, providing natural-sounding responses.  
- **Web Integration**: Opens websites, performs Google searches, and plays YouTube videos using voice commands.  
- **Weather Updates**: Dynamically retrieves current weather information through web scraping with `requests` and `BeautifulSoup`.  
- **System Commands**: Executes system tasks like opening Notepad, Calculator, Command Prompt, and more.  

## Future Enhancements  
- **Multi-Language Support**: Enable the assistant to recognize and respond in multiple languages for broader accessibility.  
- **Enhanced AI Capabilities**: Expand functionality by integrating additional APIs and improving LLM responses.  

## Contributing  
Contributions are always welcome!  
- If you'd like to contribute, please fork the repository and create a pull request.  
- For major changes, open an issue first to discuss your proposed ideas.  

### Steps to Contribute:  
1. Fork this repository.  
2. Create a new branch (`git checkout -b feature-branch-name`).  
3. Make your changes and commit (`git commit -m "Add a new feature"`).  
4. Push to the branch (`git push origin feature-branch-name`).  
5. Open a pull request and describe your changes in detail.  

We appreciate your contributions to making **Phoenix** even better!  

