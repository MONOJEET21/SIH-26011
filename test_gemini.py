import os

from dotenv import load_dotenv
from google import genai


print("1. Loading environment...")
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

print("2. API key found.")
print("3. Creating Gemini client...")

client = genai.Client(
    api_key=api_key,
    http_options={
        "timeout": 60000,
    },
)

print("4. Sending request to Gemini 3.6 Flash...")
print("   Please wait...")

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input="Say hello to the 3D ULPIN project in one sentence.",
)

print("5. Response received!")
print()
print("Gemini response:")
print(interaction.output_text)