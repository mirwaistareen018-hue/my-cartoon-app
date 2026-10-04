import streamlit as st
from google import genai

st.set_page_config(
    page_title="AI Cartoon Video Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Cartoon Video Studio")

language = st.selectbox(
    "زبان / Language",
    ["اردو", "English"]
)

script = st.text_area(
    "اپنی کہانی لکھیں:",
    placeholder="مثال: ایک بہادر بلی اپنے کتے دوست کے ساتھ جنگل میں خزانہ تلاش کرنے جاتی ہے۔",
    height=180
)

scene_count = st.slider(
    "کتنے سینز بنانے ہیں؟",
    5,
    20,
    10
)

if st.button("🎬 AI Story Director شروع کریں", type="primary"):

    if not script.strip():
        st.warning("پہلے اپنی کہانی لکھیں۔")
        st.stop()

    try:
        api_key = st.secrets["GEMINI_API_KEY"]

        client = genai.Client(api_key=api_key)

        if language == "اردو":
            prompt = f"""
آپ ایک AI Cartoon Story Director ہیں۔

اس کہانی کو {scene_count} سینز میں تقسیم کریں۔

کہانی:
{script}

ہر سین کے لیے یہ معلومات دیں:

1. Scene number
2. Scene description
3. Characters
4. Character appearance
5. Action
6. Dialogue
7. Background
8. Sound effects

کرداروں کی شکل، لباس اور بنیادی خصوصیات پوری کہانی میں مستقل رکھیں۔

جواب اردو میں دیں۔
"""
        else:
            prompt = f"""
You are an AI Cartoon Story Director.

Divide this story into {scene_count} scenes.

Story:
{script}

For every scene provide:

1. Scene number
2. Scene description
3. Characters
4. Character appearance
5. Action
6. Dialogue
7. Background
8. Sound effects

Keep character appearance, clothing and core traits consistent across all scenes.

Answer in English.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        st.success("🎉 AI Story Director نے کہانی تیار کر دی!")

        st.markdown(response.text)

    except Exception as e:
        st.error("AI Director چلانے میں مسئلہ آیا۔")
        st.code(str(e))
