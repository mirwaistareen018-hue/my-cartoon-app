import streamlit as st

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

if language == "اردو":

    script = st.text_area(
        "اپنی کہانی لکھیں:",
        placeholder="مثال: ایک بلی اور اس کا کتا دوست جنگل میں خزانہ تلاش کرنے جاتے ہیں۔",
        height=180
    )

    scene_count = st.slider(
        "کتنے سینز بنانے ہیں؟",
        5, 20, 10
    )

    button_text = "🎬 کہانی تیار کریں"

else:

    script = st.text_area(
        "Write your story:",
        placeholder="Example: A cat and his dog friend go into a forest to find treasure.",
        height=180
    )

    scene_count = st.slider(
        "Number of scenes",
        5, 20, 10
    )

    button_text = "🎬 Create Story"


if st.button(button_text, type="primary"):

    if not script.strip():

        st.warning("پہلے اپنی کہانی لکھیں۔")

    else:

        st.success("کہانی موصول ہوگئی! 🎉")

        st.header("🎭 Character Bible")

        st.write("👤 مرکزی کردار پوری کہانی میں ایک جیسا رہے گا۔")
        st.write("🎨 کردار کی شکل، لباس اور بنیادی خصوصیات برقرار رہیں گی۔")

        st.header("🎬 Scene Plan")

        for i in range(1, scene_count + 1):

            with st.expander(f"🎬 Scene {i}", expanded=True):

                st.write(f"📖 **کہانی:** {script}")

                st.write("🎭 **کردار:** مرکزی کردار")

                st.write("🖼️ **تصویر:** اس سین کا ماحول اور کردار")

                st.write("🎥 **ایکشن:** کردار اس سین میں حرکت کرے گا")

                st.write("🗣️ **ڈائیلاگ:** اس سین کی گفتگو")

                st.write("🔊 **آواز:** موسیقی اور sound effects")

        st.success("✅ Scene plan تیار ہے!")

        st.info(
            "اگلے مرحلے میں ہم اسی Scene Plan کو حقیقی AI generation سے جوڑیں گے۔"
        )
