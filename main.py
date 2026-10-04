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
        placeholder="مثال: ایک بہادر بلی جادوئی جنگل میں خزانہ تلاش کرنے جاتی ہے۔",
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
        placeholder="Example: A brave cat enters a magical forest to find a treasure.",
        height=180
    )

    scene_count = st.slider(
        "Number of Scenes",
        5,
        20,
        10
    )

    button_text = "🎬 Create Cartoon Project"


def create_scene_plan(story, count, language):

    scenes = []

    for i in range(1, count + 1):

        if language == "اردو":

            scenes.append({
                "scene": i,
                "story": f"{story} — حصہ {i}",
                "character": "مرکزی کردار",
                "image_prompt": f"2D cartoon style scene {i}, based on: {story}",
                "animation_prompt": f"Scene {i} میں کردار کی قدرتی حرکت اور camera movement",
                "dialogue": f"Scene {i} کا مکالمہ",
                "sound": f"Scene {i} کے لیے background music اور sound effects"
            })

        else:

            scenes.append({
                "scene": i,
                "story": f"{story} — Part {i}",
                "character": "Main Character",
                "image_prompt": f"2D cartoon style scene {i}, based on: {story}",
                "animation_prompt": f"Natural character movement and camera movement for scene {i}",
                "dialogue": f"Dialogue for scene {i}",
                "sound": f"Background music and sound effects for scene {i}"
            })

    return scenes


if st.button(button_text, type="primary"):

    if not script.strip():

        st.warning(
            "پہلے اپنی کہانی لکھیں۔"
            if language == "اردو"
            else "Please write your story first."
        )

    else:

        st.success(
            "✅ Cartoon Project تیار ہے!"
            if language == "اردو"
            else "✅ Cartoon Project created!"
        )

        scenes = create_scene_plan(
            script,
            scene_count,
            language
        )

        st.header("🎭 Character Bible")

        if language == "اردو":
            st.write("مرکزی کردار کی شکل، لباس اور بنیادی خصوصیات Scenes میں مستقل رکھی جائیں گی۔")
        else:
            st.write("The character's appearance, clothing and core traits will stay consistent across scenes.")

        st.header("🎬 Scene Plan")

        for item in scenes:

            with st.expander(
                f"🎬 Scene {item['scene']}",
                expanded=True
            ):

                if language == "اردو":

                    st.write(f"📖 **کہانی:** {item['story']}")
                    st.write(f"🎭 **Character:** {item['character']}")
                    st.write(f"🖼️ **Image Prompt:** {item['image_prompt']}")
                    st.write(f"🎥 **Animation:** {item['animation_prompt']}")
                    st.write(f"🗣️ **Dialogue:** {item['dialogue']}")
                    st.write(f"🔊 **Sound/Music:** {item['sound']}")

                    st.button(
                        f"🖼️ Scene {item['scene']} کی تصویر تیار کریں",
                        key=f"image_{item['scene']}"
                    )

                else:

                    st.write(f"📖 **Story:** {item['story']}")
                    st.write(f"🎭 **Character:** {item['character']}")
                    st.write(f"🖼️ **Image Prompt:** {item['image_prompt']}")
                    st.write(f"🎥 **Animation:** {item['animation_prompt']}")
                    st.write(f"🗣️ **Dialogue:** {item['dialogue']}")
                    st.write(f"🔊 **Sound/Music:** {item['sound']}")

                    st.button(
                        f"🖼️ Generate Scene {item['scene']} Image",
                        key=f"image_{item['scene']}"
                    )

        st.divider()

        st.header("🚧 AI Generation Pipeline")

        st.write("📝 Story → 🎬 Scenes → 🖼️ Images → 🎥 Animation → 🗣️ Voice → 🎵 Music → ✂️ Editing → 🎞️ MP4")

        st.info(
            "اگلے مرحلے میں ہم ان Image buttons کو حقیقی مفت/اوپن image-generation system سے جوڑیں گے۔"
            if language == "اردو"
            else "Next, we will connect these image buttons to a free/open image-generation system."
                    )
