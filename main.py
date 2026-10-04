import streamlit as st
from huggingface_hub import InferenceClient

st.set_page_config(
    page_title="AI Cartoon Video Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Cartoon Video Studio")


# -----------------------------
# Hugging Face Image Generator
# -----------------------------

def generate_image(prompt):

    token = st.secrets.get("HF_TOKEN")

    if not token:
        return None, "HF_TOKEN نہیں ملا۔ Streamlit Secrets چیک کریں۔"

    try:
        client = InferenceClient(
            api_key=token,
            provider="auto"
        )

        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )

        return image, None

    except Exception as e:
        return None, str(e)


# -----------------------------
# Language
# -----------------------------

language = st.selectbox(
    "زبان / Language",
    ["اردو", "English"]
)


# -----------------------------
# Story Input
# -----------------------------

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


# -----------------------------
# Scene Planner
# -----------------------------

def create_scene_plan(story, count, language):

    scenes = []

    for i in range(1, count + 1):

        if language == "اردو":

            scenes.append({
                "scene": i,
                "story": f"{story} — حصہ {i}",
                "character": "مرکزی کردار",

                "image_prompt": (
                    f"2D colorful cartoon scene, scene {i}, "
                    f"cute main character, consistent character design, "
                    f"cinematic composition, detailed background, "
                    f"based on this story: {story}"
                ),

                "animation_prompt":
                    f"Natural character movement and camera movement for scene {i}",

                "dialogue":
                    f"Scene {i} کا مکالمہ",

                "sound":
                    f"Scene {i} کے لیے background music اور sound effects"
            })

        else:

            scenes.append({
                "scene": i,
                "story": f"{story} — Part {i}",
                "character": "Main Character",

                "image_prompt": (
                    f"2D colorful cartoon scene, scene {i}, "
                    f"cute main character, consistent character design, "
                    f"cinematic composition, detailed background, "
                    f"based on this story: {story}"
                ),

                "animation_prompt":
                    f"Natural character movement and camera movement for scene {i}",

                "dialogue":
                    f"Dialogue for scene {i}",

                "sound":
                    f"Background music and sound effects for scene {i}"
            })

    return scenes


# -----------------------------
# Create Project
# -----------------------------

if st.button(button_text, type="primary"):

    if not script.strip():

        st.warning(
            "پہلے اپنی کہانی لکھیں۔"
            if language == "اردو"
            else "Please write your story first."
        )

    else:

        scenes = create_scene_plan(
            script,
            scene_count,
            language
        )

        st.success(
            "✅ Cartoon Project تیار ہے!"
            if language == "اردو"
            else "✅ Cartoon Project created!"
        )

        st.header("🎭 Character Bible")

        if language == "اردو":
            st.write(
                "مرکزی کردار کی شکل، لباس اور بنیادی خصوصیات Scenes میں مستقل رکھی جائیں گی۔"
            )
        else:
            st.write(
                "The character's appearance, clothing and core traits "
                "will stay consistent across scenes."
            )

        st.header("🎬 Scene Plan")

        for item in scenes:

            with st.expander(
                f"🎬 Scene {item['scene']}",
                expanded=True
            ):

                st.write(f"📖 **Story:** {item['story']}")
                st.write(f"🎭 **Character:** {item['character']}")
                st.write(f"🖼️ **Image Prompt:** {item['image_prompt']}")
                st.write(f"🎥 **Animation:** {item['animation_prompt']}")
                st.write(f"🗣️ **Dialogue:** {item['dialogue']}")
                st.write(f"🔊 **Sound/Music:** {item['sound']}")

                # REAL IMAGE BUTTON
                if st.button(
                    f"🖼️ Generate Scene {item['scene']} Image",
                    key=f"generate_image_{item['scene']}"
                ):

                    with st.spinner(
                        "🎨 AI تصویر بنا رہا ہے..."
                        if language == "اردو"
                        else "🎨 Generating AI image..."
                    ):

                        image, error = generate_image(
                            item["image_prompt"]
                        )

                    if image is not None:

                        st.image(
                            image,
                            caption=f"Scene {item['scene']}"
                        )

                    else:

                        st.error(
                            f"❌ Image generation error: {error}"
                        )

        st.divider()

        st.header("🚧 AI Generation Pipeline")

        st.write(
            "📝 Story → 🎬 Scenes → 🖼️ Images → 🎥 Animation → "
            "🗣️ Voice → 🎵 Music → ✂️ Editing → 🎞️ MP4"
    )
