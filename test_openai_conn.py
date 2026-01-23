import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("BASE_URL =", os.getenv("OPENAI_API_BASE_URL"))
print("KEY SET  =", bool(os.getenv("OPENAI_API_KEY")))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)

print(client.models.list())
