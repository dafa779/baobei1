from deep_translator import GoogleTranslator

def translate(text, target):
    return GoogleTranslator(source='auto', target=target).translate(text)
