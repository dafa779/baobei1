from deep_translator import GoogleTranslator

def translate_to_vi(text):
    return GoogleTranslator(source='auto', target='vi').translate(text)

def translate_to_zh(text):
    return GoogleTranslator(source='auto', target='zh-CN').translate(text)
