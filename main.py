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

    st.header("📝 اپنی کہانی لکھیں")

    script = st.text_area(
        "کہانی:",
        placeholder="مثال: ایک بہادر بلی اپنے کتے دوست کے ساتھ جادوئی جنگل میں خزانہ تلاش کرنے جاتی ہے۔",
        height=180
    )

    scene_count = st.slider(
        "کتنے سینز؟",
        5,
        20,
        10
    )

    button_text = "🎬 کارٹون پروجیکٹ بنائیں"

else:

    st.header("📝 Write Your Story")

    script = st.text_area(
        "Story:",
        placeholder="Example: A brave cat and his dog friend enter a magical forest to find treasure.",
        height=180
    )

    scene_count = st.slider(
        "Number of Scenes",
        5,
        20,
        10
    )

    button_text = "🎬 Create Cartoon Project"


if st.button(button_text, type="primary"):

    if not script.strip():

        if language == "اردو":
            st.warning("پہلے اپنی کہانی لکھیں۔")
        else:
            st.warning("Please write your story first.")

    else:

        st.success("✅ پروجیکٹ تیار ہے!")

        st.header("🎭 Character Bible")

        if language == "اردو":
            st.write("مرکزی کردار پوری کہانی میں ایک جیسا رہے گا۔")
            st.write("لباس، شکل اور بنیادی خصوصیات مستقل رہیں گی۔")
        else:
            st.write("The main character will remain consistent.")
            st.write("Appearance, clothing and core traits will stay consistent.")

        st.header("🎬 Scene Plan")

        for i in range(1, scene_count + 1):

            with st.expander(f"🎬 Scene {i}", expanded=True):

                st.write(f"📖 **Story:** {script}")
                st.write("🎭 **Character:** Main character")
                st.write("🖼️ **Image:** Scene artwork")
                st.write("🎥 **Animation:** Character movement")
                st.write("🗣️ **Dialogue:** Scene dialogue")
                st.write("🔊 **Sound:** Music and sound effects")

        st.success("🎉 Scene Plan مکمل ہے!")

        st.info(
            "اگلے مرحلے میں ہم اس Scene Plan کو حقیقی تصویر، آواز اور ویڈیو generation سے جوڑیں گے۔"
        )
