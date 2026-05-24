"""

LLM initialization for the OmniAgent system.

Note : for now(initial development phase) we will only use google gemini 2.5 flash (free api)

"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

#setting up environment variables
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_GEMINI_API_KEY")

# llm logic
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", 
                                  temperature=0.6)