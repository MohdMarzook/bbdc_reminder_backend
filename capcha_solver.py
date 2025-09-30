import requests
import re
from io import BytesIO
import base64
import pytesseract
from PIL import Image, ImageFilter,  ImageChops


# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  

def solve_captcha(image_data):
    try:
        data = image_data
        image_data = re.sub('^data:image/.+;base64,', '', data)
        img = Image.open(BytesIO(base64.b64decode(image_data)))

        img = img.convert('L')
        width, height = img.size  
        threshold = 220
        out = img.point(lambda p: 255 if p > threshold else 0)
        out = out.filter(ImageFilter.GaussianBlur(radius=1))
        out = out.resize((width*5, height*5), Image.NEAREST)
        out = out.filter(ImageFilter.SHARPEN)
        out = out.resize((int(width*2), int(height*2)), Image.NEAREST)
        threshold = 35
        out = out.point(lambda p: 255 if p > threshold else 0)
        out = out.filter(ImageFilter.SMOOTH_MORE)
        
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        text = pytesseract.image_to_string(out, config=custom_config)
        # print(f"Raw OCR Output: '{text[:-1]}'")

        solved_text = "".join(filter(str.isalnum, text))
        
        return solved_text if solved_text else "Failed to extract text."

    except FileNotFoundError:
        return f"Error: Image file not found at '{image_data}'"
    except requests.exceptions.RequestException as e:
        return f"Error: Could not download image from URL. {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
