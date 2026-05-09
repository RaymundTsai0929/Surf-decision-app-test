import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("錯誤：找不到 GOOGLE_API_KEY")
else:
    genai.configure(api_key=api_key)
    print("正在列出可用的模型...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"模型名稱: {m.name}")
    except Exception as e:
        print(f"發生錯誤: {e}")
