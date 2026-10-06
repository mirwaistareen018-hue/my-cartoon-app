import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

mera_script = "ایک چھوٹا خرگوش تھا جو جنگل میں رہتا تھا۔ وہ ہمیشہ دوسروں کی مدد کرتا تھا۔"

prompt = "تم ایک بچوں کے کہانی لکھنے والے ہو۔ اس سکرپٹ کو 3 منٹ کی مکمل کہانی بنا دو، بچوں کے لیے سادہ اردو میں: " + mera_script

print("کہانی بن رہی ہے... براہ کرم انتظار کریں...")
print()

response = model.generate_content(prompt)

print("=" * 40)
print("آپ کی کہانی:")
print("=" * 40)
print()
print(response.text)
