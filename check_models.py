
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list()

    print("Available Groq models:")
    for model in models.data:
        print("-", model.id)

except Exception as error:
    print("Error type:", type(error).__name__)
    print("Details:", str(error))
