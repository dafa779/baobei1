from deep_translator import GoogleTranslator

def translate(text):
    try:
        # phát hiện tiếng
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            # Trung → Việt
            result = GoogleTranslator(source='zh-CN', target='vi').translate(text)
        else:
            # Việt → Trung
            result = GoogleTranslator(source='vi', target='zh-CN').translate(text)

        return result

    except Exception as e:
        return "Lỗi dịch: " + str(e)
