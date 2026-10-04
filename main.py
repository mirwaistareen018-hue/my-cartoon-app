import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import os

st.set_page_config(
    page_title="AI Cartoon Video Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Cartoon Video Studio")

# ==================================================
# SESSION STATE
# ==================================================

if "scenes" not in st.session_state:
    st.session_state.scenes = []

if "generated_images" not in st.session_state:
    st.session_state.generated_images = {}

if "video_files" not in st.session_state:
    st.session_state.video_files = {}

if "project_created" not in st.session_state:
    st.session_state.project_created = False


# ==================================================
# HUGGING FACE IMAGE GENERATOR
# ==================================================

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


# ==================================================
# CREATE SIMPLE ANIMATED VIDEO
# ==================================================

def create_video(image, output_path, duration=5):

    try:

        from moviepy import ImageClip

        image_path = output_path.replace(".mp4", ".png")

        image.save(image_path)

        clip = ImageClip(image_path).with_duration(duration)

        clip = clip.resized(height=720)

        clip = clip.with_position("center")

        clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio=False
        )

        clip.close()

        return True, None

    except Exception as e:

        return False, str(e)


# ==================================================
# LANGUAGE
# ==================================================

language = st.selectbox(
    "زبان / Language",
    ["اردو", "English"]
)


# ==================================================
# STORY INPUT
# ==================================================

if language == "اردو":

    st.header("📝 اپنی کہانی لکھیں")

    script = st.text_area(
        "کہانی:",
        placeholder="مثال: ایک پیاری مرغی اپنے بچوں کے ساتھ کھیت میں جاتی ہے۔",
        height=180
    )

    scene_count = st.slider(
        "کتنے Scenes؟",
        1,
        10,
        5
    )

    button_text = "🎬 Cartoon Project بنائیں"

else:

    st.header("📝 Write Your Story")

    script = st.text_area(
        "Story:",
        placeholder="Example: A cute hen goes to the farm with her chicks.",
        height=180
    )

    scene_count = st.slider(
        "Number of Scenes",
        1,
        10,
        5
    )

    button_text = "🎬 Create Cartoon Project"


# ==================================================
# CREATE SCENE PLAN
# ==================================================

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
                    f"cute hen, consistent character design, "
                    f"cinematic composition, detailed background, "
                    f"based on this story: {story}"
                ),

                "animation_prompt":
                    f"Scene {i} میں مرغی کی ہلکی قدرتی حرکت اور camera movement",

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
                    f"cute hen, consistent character design, "
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


# ==================================================
# CREATE PROJECT
# ==================================================

if st.button(button_text, type="primary"):

    if not script.strip():

        st.warning(
            "پہلے اپنی کہانی لکھیں۔"
            if language == "اردو"
            else "Please write your story first."
        )

    else:

        st.session_state.scenes = create_scene_plan(
            script,
            scene_count,
            language
        )

        st.session_state.generated_images = {}
        st.session_state.video_files = {}
        st.session_state.project_created = True


# ==================================================
# SHOW PROJECT
# ==================================================

if st.session_state.project_created:

    st.success(
        "✅ Cartoon Project تیار ہے!"
        if language == "اردو"
        else "✅ Cartoon Project created!"
    )

    st.header("🎭 Character Bible")

    st.write(
        "مرکزی کردار کی شکل، لباس اور بنیادی خصوصیات "
        "تمام Scenes میں مستقل رکھی جائیں گی۔"
        if language == "اردو"
        else
        "The character's appearance, clothing and core traits "
        "will stay consistent across scenes."
    )

    st.header("🎬 Scene Plan")

    for item in st.session_state.scenes:

        scene_number = item["scene"]

        with st.expander(
            f"🎬 Scene {scene_number}",
            expanded=True
        ):

            st.write(
                f"📖 **Story:** {item['story']}"
            )

            st.write(
                f"🎭 **Character:** {item['character']}"
            )

            st.write(
                f"🖼️ **Image Prompt:** {item['image_prompt']}"
            )

            # ==========================================
            # IMAGE
            # ==========================================

            if scene_number in st.session_state.generated_images:

                st.image(
                    st.session_state.generated_images[scene_number],
                    caption=f"Scene {scene_number}"
                )

            # ==========================================
            # GENERATE IMAGE
            # ==========================================

            if st.button(
                f"🖼️ Generate Scene {scene_number} Image",
                key=f"generate_image_{scene_number}"
            ):

                with st.spinner(
                    "🎨 AI تصویر بنا رہا ہے..."
                    if language == "اردو"
                    else
                    "🎨 Generating AI image..."
                ):

                    image, error = generate_image(
                        item["image_prompt"]
                    )

                if image is not None:

                    st.session_state.generated_images[
                        scene_number
                    ] = image

                    st.rerun()

                else:

                    st.error(
                        f"❌ Image generation error: {error}"
                    )

            # ==========================================
            # CREATE VIDEO
            # ==========================================

            if scene_number in st.session_state.generated_images:

                if st.button(
                    f"🎥 Scene {scene_number} کو Video بنائیں",
                    key=f"video_{scene_number}"
                ):

                    os.makedirs("videos", exist_ok=True)

                    output_path = (
                        f"videos/scene_{scene_number}.mp4"
                    )

                    with st.spinner(
                        "🎥 تصویر سے ویڈیو بن رہی ہے..."
                    ):

                        success, error = create_video(
                            st.session_state.generated_images[
                                scene_number
                            ],
                            output_path
                        )

                    if success:

                        st.session_state.video_files[
                            scene_number
                        ] = output_path

                        st.success(
                            "✅ Scene کی MP4 ویڈیو تیار ہے!"
                        )

                    else:

                        st.error(
                            f"❌ Video error: {error}"
                        )

            # ==========================================
            # SHOW VIDEO
            # ==========================================

            if scene_number in st.session_state.video_files:

                video_path = st.session_state.video_files[
                    scene_number
                ]

                st.video(video_path)

                with open(video_path, "rb") as video_file:

                    st.download_button(
                        "⬇️ MP4 Download کریں",
                        video_file,
                        file_name=f"scene_{scene_number}.mp4",
                        mime="video/mp4",
                        key=f"download_{scene_number}"
                    )


# ==================================================
# PIPELINE
# ==================================================

st.divider()

st.header("🚧 AI Generation Pipeline")

st.write(
    "📝 Story → 🎬 Scenes → 🖼️ Images → "
    "🎥 Animation → 🗣️ Voice → 🎵 Music → "
    "✂️ Editing → 🎞️ MP4"
                    )
