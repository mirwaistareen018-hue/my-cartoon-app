import streamlit as st

st.set_page_config(
    page_title="My AI Cartoon Videos",
    page_icon="🎬",
    layout="wide"
)

language = st.selectbox(
    "Language / زبان",
    ["English", "اردو"]
)

if language == "English":
    st.title("🎬 My AI Cartoon Video Studio")
    st.write("Script → AI Director → Scenes")

    script = st.text_area(
        "Write your story or script:",
        placeholder="Example: A cat goes into a forest with its friend to find a treasure.",
        height=150
    )

    scene_count = st.slider(
        "Number of Scenes",
        min_value=5,
        max_value=20,
        value=10
    )

    button_text = "🎬 Start AI Director"

else:
    st.title("🎬 میری AI کارٹون ویڈیو اسٹوڈیو")
    st.write("اسکرپٹ → AI ڈائریکٹر → سینز")

    script = st.text_area(
        "اپنی کہانی یا اسکرپٹ لکھیں:",
        placeholder="مثال: ایک بلی اپنے دوست کے ساتھ جنگل میں خزانہ تلاش کرنے جاتی ہے۔",
        height=150
    )

    scene_count = st.slider(
        "سینز کی تعداد",
        min_value=5,
        max_value=20,
        value=10
    )

    button_text = "🎬 AI ڈائریکٹر شروع کریں"


if st.button(button_text, type="primary"):

    if not script.strip():

        if language == "English":
            st.warning("Please write your story first.")
        else:
            st.warning("پہلے اپنی کہانی لکھیں۔")

    else:

        if language == "English":
            st.success("AI Director created the scenes! ✅")
        else:
            st.success("AI ڈائریکٹر نے سینز تیار کر دیے! ✅")

        for i in range(1, scene_count + 1):

            st.subheader(f"🎬 Scene {i}")

            if language == "English":
                st.write(f"📖 Story: {script}")
                st.write("🎭 Character: The main character stays consistent.")
                st.write("🖼️ Image: Scene environment, character and action.")
                st.write("🎥 Animation: Character movement and scene animation.")
                st.write("🗣️ Dialogue: Character dialogue for this scene.")
                st.write("🔊 Sound: Music and sound effects.")

            else:
                st.write(f"📖 کہانی: {script}")
                st.write("🎭 کردار: مرکزی کردار ایک جیسا رہے گا۔")
                st.write("🖼️ تصویر: اس سین کا ماحول، کردار اور ایکشن۔")
                st.write("🎥 اینیمیشن: کردار کی حرکت اور سین کی animation۔")
                st.write("🗣️ ڈائیلاگ: اس سین میں کردار کی گفتگو۔")
                st.write("🔊 آواز: موسیقی اور sound effects۔")

            st.divider()
