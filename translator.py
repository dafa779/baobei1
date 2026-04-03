from googletrans import Translator

translator = Translator()

def translate(text):

    detect = translator.detect(text).lang

    if detect == "zh-cn" or detect == "zh-tw":
        result = translator.translate(text, src="zh-cn", dest="vi")
    elif detect == "vi":
        result = translator.translate(text, src="vi", dest="zh-cn")
    else:
        result = translator.translate(text, dest="vi")

    return result.text
