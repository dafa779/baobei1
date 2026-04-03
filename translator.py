from deep_translator import GoogleTranslator

def translate(text, target):
    translated = GoogleTranslator(source='auto', target=target).translate(text)
    return translated
