import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="My AI Cartoon Videos", page_icon="🎬")

st.title("🎬 My AI Cartoon Videos")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key or api_key == "YOUR_API_KEY_HERE":
    st.error("OpenAI API key ابھی configure نہیں ہوئی۔")
else:
    client = OpenAI(api_key=api_key)

    st.success("OpenAI API key مل گئی! ✅")

    if st.button("Test OpenAI Connection"):
        try:
            response = client.responses.create(
                model="gpt-4o-mini"
                input="Say hello in one short sentence."
            )

            st.success("OpenAI connection successful! 🎉")
            st.write(response.output_text)

        except Exception as e:
            st.error(f"API Error: {e}")
