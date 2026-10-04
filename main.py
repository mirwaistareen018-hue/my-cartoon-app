import streamlit as st
from huggingface_hub import InferenceClient
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

if "generated_videos" not in st.session_state:
    st.session_state.generated_videos = {}

if "project_created" not in st.session_state:
    st.session_state.project_created = False


# ==================================================
# HUGGING FACE CLIENT
# ==================================================

def get_client():

    token = st.secrets.get("HF_TOKEN")

    if not token:
        return None

    return InferenceClient(
        api_key=token,
        provider="auto"
    )


# ==================================================
# AI IMAGE GENERATOR
# ==================================================

def generate_image(prompt):

    client = get_client()

    if client is None:
        return None, "HF_TOKEN نہیں ملا۔ Streamlit Secrets چیک کریں۔"

    try:

        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )

        return image, None

    except Exception as e:

        return None, str(e)


# ==================================================
# AI IMAGE TO VIDEO
# ==================================================

def generate_ai_video(image, motion_prompt):

    client = get_client()

    if client is None:
        return None, "HF_TOKEN نہیں ملا۔"

    try:

        video = client.image_to_video(
            image=image,
            prompt=motion_prompt,
            model="Wan-AI/Wan2.2-I2V-A14B"
        )

        return video, None

    except Exception as e:

        return None, str(e)


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
# SCENE PLAN
# ==================================================

def create_scene_plan(story, count, language):

    scenes = []

    for i in range(1, count + 1):

        if language == "اردو":

            scenes.append({

                "scene": i,

                "story": f"{story} — حصہ {i}",

                "character": "پیاری مرغی اور اس کا بچہ",

                "image_prompt": (
                    f"2D colorful children's cartoon, "
                    f"scene {i}, a cute mother hen and her chick, "
                    f"consistent character design, "
                    f"bright colors, detailed farm background, "
                    f"cinematic composition, "
                    f"based on this story: {story}"
                ),

                "motion_prompt": (
                    "A cute mother hen gently moves her head and body, "
                    "her little chick walks naturally beside her, "
                    "the chick looks around curiously, "
                    "their feathers move slightly in a gentle breeze, "
                    "grass and leaves move naturally, "
                    "smooth subtle character motion, "
                    "slow cinematic camera movement, "
                    "stable cartoon style, "
                    "keep the same characters and appearance, "
                    "no morphing, no deformation, "
                    "no extra characters."
                )

            })

        else:

            scenes.append({

                "scene": i,

                "story": f"{story} — Part {i}",

                "character": "Cute mother hen and her chick",

                "image_prompt": (
                    f"2D colorful children's cartoon, "
                    f"scene {i}, a cute mother hen and her chick, "
                    f"consistent character design, "
                    f"bright colors, detailed farm background, "
                    f"cinematic composition, "
                    f"based on this story: {story}"
                ),

                "motion_prompt": (
                    "A cute mother hen gently moves her head and body, "
                    "her little chick walks naturally beside her, "
                    "the chick looks around curiously, "
                    "their feathers move slightly in a gentle breeze, "
                    "grass and leaves move naturally, "
                    "smooth subtle character motion, "
                    "slow cinematic camera movement, "
                    "stable cartoon style, "
                    "keep the same characters and appearance, "
                    "no morphing, no deformation, "
                    "no extra characters."
                )

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
            else
            "Please write your story first."
        )

    else:

        st.session_state.scenes = create_scene_plan(
            script,
            scene_count,
            language
        )

        st.session_state.generated_images = {}
        st.session_state.generated_videos = {}
        st.session_state.project_created = True


# ==================================================
# SHOW PROJECT
# ==================================================

if st.session_state.project_created:

    st.success(
        "✅ Cartoon Project تیار ہے!"
        if language == "اردو"
        else
        "✅ Cartoon Project created!"
    )

    st.header("🎭 Character Bible")

    st.write(
        "مرکزی کردار: پیاری مرغی اور اس کا بچہ۔ "
        "ہم کوشش کریں گے کہ تمام Scenes میں ان کی شکل مستقل رہے۔"
        if language == "اردو"
        else
        "Main characters: a cute mother hen and her chick. "
        "We will try to keep their appearance consistent across scenes."
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

            st.write(
                f"🎥 **Motion Prompt:** {item['motion_prompt']}"
            )


            # ==========================================
            # EXISTING IMAGE
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
                f"🖼️ Scene {scene_number} کی تصویر بنائیں",
                key=f"image_{scene_number}"
            ):

                with st.spinner(
                    "🎨 AI تصویر بنا رہا ہے..."
                ):

                    image, error = generate_image(
                        item["image_prompt"]
                    )

                if image is not None:

                    st.session_state.generated_images[
                        scene_number
                    ] = image

                    st.success("✅ تصویر تیار ہے!")

                    st.rerun()

                else:

                    st.error(
                        f"❌ Image Error: {error}"
                    )


            # ==========================================
            # AI MOTION VIDEO
            # ==========================================

            if scene_number in st.session_state.generated_images:

                if st.button(
                    f"🤖 Scene {scene_number} کو AI Motion Video بنائیں",
                    key=f"motion_{scene_number}"
                ):

                    with st.spinner(
                        "🤖 AI مرغی اور بچے کو حرکت دے رہا ہے..."
                    ):

                        video, error = generate_ai_video(
                            st.session_state.generated_images[
                                scene_number
                            ],
                            item["motion_prompt"]
                        )

                    if video is not None:

                        os.makedirs(
                            "videos",
                            exist_ok=True
                        )

                        video_path = (
                            f"videos/scene_{scene_number}_ai.mp4"
                        )

                        try:

                            if isinstance(video, bytes):

                                video_bytes = video

                            elif hasattr(video, "read"):

                                video_bytes = video.read()

                            else:

                                video_bytes = bytes(video)

                            with open(
                                video_path,
                                "wb"
                            ) as f:

                                f.write(video_bytes)

                            st.session_state.generated_videos[
                                scene_number
                            ] = video_path

                            st.success(
                                "🎉 AI Motion Video تیار ہو گئی!"
                            )

                        except Exception as save_error:

                            st.error(
                                f"❌ Video Save Error: {save_error}"
                            )

                    else:

                        st.error(
                            f"❌ AI Video Error: {error}"
                        )


            # ==========================================
            # SHOW AI VIDEO
            # ==========================================

            if scene_number in st.session_state.generated_videos:

                video_path = (
                    st.session_state.generated_videos[
                        scene_number
                    ]
                )

                st.video(video_path)

                with open(
                    video_path,
                    "rb"
                ) as video_file:

                    st.download_button(
                        "⬇️ AI Video Download کریں",
                        video_file,
                        file_name=(
                            f"scene_{scene_number}_ai.mp4"
                        ),
                        mime="video/mp4",
                        key=f"download_ai_{scene_number}"
                    )


# ==================================================
# PIPELINE
# ==================================================

st.divider()

st.header("🚧 AI Generation Pipeline")

st.write(
    "📝 Story → 🎬 Scenes → 🖼️ AI Images → "
    "🤖 AI Motion → 🗣️ Voice → 👄 Lip Sync → "
    "🎵 Music → ✂️ Editing → 🎞️ Final MP4"
    )               )


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
