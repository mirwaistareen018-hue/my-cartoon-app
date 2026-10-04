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
        "کتنے Scenes؟",
        5,
        20,
        10
    )

    button_text = "🎬 Cartoon Project بنائیں"

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


def make_scenes(story, count, language):
    sentences = [
        s.strip()
        for s in story.replace("۔", ".").split(".")
        if s.strip()
    ]

    if not sentences:
        sentences = [story.strip()]

    scenes = []

    for i in range(count):
        part = sentences[i % len(sentences)]

        if language == "اردو":
            scenes.append(
                f"Scene {i + 1}: {part}"
            )
        else:
            scenes.append(
                f"Scene {i + 1}: {part}"
            )

    return scenes


if st.button(button_text, type="primary"):

    if not script.strip():

        if language == "اردو":
            st.warning("پہلے اپنی کہانی لکھیں۔")
        else:
            st.warning("Please write your story first.")

    else:

        st.success("✅ Cartoon Project تیار ہے!")

        st.header("🎭 Character Bible")

        if language == "اردو":
            st.write("مرکزی کردار پوری کہانی میں ایک جیسا رہے گا۔")
            st.write("شکل، لباس اور بنیادی خصوصیات مستقل رہیں گی۔")
        else:
            st.write("The main character will remain consistent throughout the story.")
            st.write("Appearance, clothing and core traits will stay consistent.")

        st.header("🎬 Scene Plan")

        scenes = make_scenes(
            script,
            scene_count,
            language
        )

        for scene in scenes:

            with st.expander(
                f"🎬 {scene.split(':')[0]}",
                expanded=True
            ):

                scene_text = scene.split(":", 1)[1].strip()

                if language == "اردو":
                    st.write(f"📖 **کہانی:** {scene_text}")
                    st.write("🎭 **کردار:** Main Character")
                    st.write("🖼️ **تصویر:** Scene Artwork")
                    st.write("🎥 **Animation:** Character Movement")
                    st.write("🗣️ **Dialogue:** Scene Dialogue")
                    st.write("🔊 **Sound:** Music & Sound Effects")

                else:
                    st.write(f"📖 **Story:** {scene_text}")
                    st.write("🎭 **Character:** Main Character")
                    st.write("🖼️ **Image:** Scene Artwork")
                    st.write("🎥 **Animation:** Character Movement")
                    st.write("🗣️ **Dialogue:** Scene Dialogue")
                    st.write("🔊 **Sound:** Music & Sound Effects")

        if language == "اردو":
            st.success("🎉 کہانی Scenes میں تقسیم ہو گئی!")
        else:
            st.success("🎉 Story has been divided into scenes!")

        st.info(
            "اگلے مرحلے میں ہم Scenes کو حقیقی AI تصاویر سے جوڑیں گے۔"
            if language == "اردو"
            else "In the next step, we will connect the scenes to real AI image generation."
        )
