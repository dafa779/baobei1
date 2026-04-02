from openai import OpenAI
from langdetect import detect
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def translate(text,target="vi"):

    try:
        source=detect(text)
    except:
        source="auto"

    prompt=f"Translate from {source} to {target}:\n{text}"

    response=client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content
