from openai import OpenAI
import os
from langdetect import detect

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate(text):

    try:
        lang = detect(text)
    except:
        lang = "auto"

    if lang == "zh-cn" or lang == "zh":
        target = "Vietnamese"
    else:
        target = "Chinese"

    prompt = f"Translate this text to {target}:\n{text}"

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
