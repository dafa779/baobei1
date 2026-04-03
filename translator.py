from googletrans import Translator

translator = Translator()

def translate(text, target):
    result = translator.translate(text, dest=target)
    return result.text
