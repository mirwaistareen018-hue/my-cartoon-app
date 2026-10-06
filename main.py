import streamlit as st
import google.generativeai as genai

api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-pro')

st.title("🎨 میری کارٹون کہانی ایپ")

mera_script = st.text_area(
    "اپنا سکرپٹ یہاں لکھیں:",
    "ایک چھوٹا خرگوش تھا جو جنگل میں رہتا تھا۔"
)

if st.button("کہانی بنائیں"):
    if mera_script:
        with st.spinner("کہانی بن رہی ہے..."):
            prompt = "تم ایک بچوں کے کہانی لکھنے والے ہو۔ اس سکرپٹ کو 3 منٹ کی مکمل کہانی بنا دو، بچوں کے لیے سادہ اردو میں: " + mera_script
            
            response = model.generate_content(prompt)
            
            st.subheader("📖 آپ کی کہانی:")
            st.write(response.text)
    else:
        st.warning("پہلے سکرپٹ لکھیں!")
