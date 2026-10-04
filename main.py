import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import time

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
# AI IMAGE TO VIDEO
# ==================================================

def create_ai_video(image, motion_prompt, scene_number):

    try:

        from gradio_client import Client, handle_file
        import tempfile

        os.makedirs("videos", exist_ok=True)

        # ------------------------------------------
        # Save image temporarily
        # ------------------------------------------

        temp_image = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        )

        temp_image_path = temp_image.name

        image.save(temp_image_path)

        temp_image.close()


        # ------------------------------------------
        # Connect to free Hugging Face ZeroGPU Space
        # ------------------------------------------

        client = Client(
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
        )


        # ------------------------------------------
        # Strong animation prompt
        # ------------------------------------------

        prompt = (
            motion_prompt
            + ", smooth natural character movement, "
            "subtle body movement, natural head movement, "
            "environment movement, cinematic camera movement, "
            "continuous animation, stable character appearance"
        )


        negative_prompt = (
            "static image, frozen frame, "
            "no movement, blurry, distorted, "
            "deformed character, extra limbs, "
            "flickering, unstable face, "
            "warped body, bad anatomy"
        )


        # ------------------------------------------
        # Send image to Wan 2.2
        # ------------------------------------------

        result = client.predict(
            handle_file(temp_image_path),
            prompt,
            6,
            negative_prompt,
            3.5,
            1,
            1,
            42,
            True,
            api_name="/generate_video"
        )


        # ------------------------------------------
        # Get generated video
        # ------------------------------------------

        generated_video = result[0] if isinstance(
            result,
            (list, tuple)
        ) else result


        if not generated_video:
            return None, "AI نے video file واپس نہیں کی۔"


        # ------------------------------------------
        # Copy generated video to our project
        # ------------------------------------------

        video_path = (
            f"videos/scene_{scene_number}_ai.mp4"
        )

        if isinstance(generated_video, str):

            shutil.copyfile(
                generated_video,
                video_path
            )

        else:

            return None, (
                "AI video response کا format سمجھ نہیں آیا۔"
            )


        # ------------------------------------------
        # Cleanup
        # ------------------------------------------

        try:
            os.remove(temp_image_path)
        except:
            pass


        return video_path, None


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
        placeholder=(
            "مثال: ایک پیاری مرغی اپنے بچوں کے ساتھ "
            "کھیت میں جاتی ہے۔"
        ),
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
        placeholder=(
            "Example: A cute hen goes to the farm "
            "with her chicks."
        ),
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

            scene = {
                "scene": i,

                "story": f"{story} — حصہ {i}",

                "character": (
                    "پیاری مرغی اور اس کا چھوٹا بچہ"
                ),

                "image_prompt": (
                    "2D colorful children's cartoon, "
                    "cute mother hen and her little chick, "
                    "bright green farm environment, "
                    "consistent character design, "
                    "friendly expressions, "
                    "cinematic composition, "
                    f"story: {story}, "
                    f"scene {i}"
                ),

                "animation_prompt": (
                    "The mother hen gently moves her head "
                    "and body, the little chick walks and "
                    "moves naturally beside her, "
                    "their feathers move gently in the breeze, "
                    "grass and plants move softly, "
                    "clouds move slowly in the background, "
                    "gentle cinematic camera movement"
                )
            }

        else:

            scene = {
                "scene": i,

                "story": f"{story} — Part {i}",

                "character": (
                    "Cute mother hen and her little chick"
                ),

                "image_prompt": (
                    "2D colorful children's cartoon, "
                    "cute mother hen and her little chick, "
                    "bright green farm environment, "
                    "consistent character design, "
                    "friendly expressions, "
                    "cinematic composition, "
                    f"story: {story}, "
                    f"scene {i}"
                ),

                "animation_prompt": (
                    "The mother hen gently moves her head "
                    "and body, the little chick walks and "
                    "moves naturally beside her, "
                    "their feathers move gently in the breeze, "
                    "grass and plants move softly, "
                    "clouds move slowly in the background, "
                    "gentle cinematic camera movement"
                )
            }

        scenes.append(scene)

    return scenes


# ==================================================
# CREATE PROJECT
# ==================================================

if st.button(button_text, type="primary"):

    if not script.strip():

        if language == "اردو":
            st.warning("پہلے اپنی کہانی لکھیں۔")
        else:
            st.warning("Please write your story first.")

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

    if language == "اردو":
        st.success("✅ Cartoon Project تیار ہے!")
    else:
        st.success("✅ Cartoon Project created!")


    # ==================================================
    # CHARACTER BIBLE
    # ==================================================

    st.header("🎭 Character Bible")

    if language == "اردو":

        st.write(
            "مرکزی کردار: پیاری مرغی اور اس کا بچہ۔ "
            "ہم Scenes میں ان کی شکل کو مستقل رکھنے "
            "کی کوشش کریں گے۔"
        )

    else:

        st.write(
            "Main characters: a cute mother hen and "
            "her chick."
        )


    # ==================================================
    # SCENE PLAN
    # ==================================================

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
                f"🖼️ **Image Prompt:** "
                f"{item['image_prompt']}"
            )

            st.write(
                f"🎥 **Animation Plan:** "
                f"{item['animation_prompt']}"
            )


            # ==========================================
            # SHOW IMAGE
            # ==========================================

            if scene_number in st.session_state.generated_images:

                st.image(
                    st.session_state.generated_images[
                        scene_number
                    ],
                    caption=f"Scene {scene_number}"
                )


            # ==========================================
            # IMAGE BUTTON
            # ==========================================

            if st.button(
                f"🖼️ Scene {scene_number} کی تصویر بنائیں",
                key=f"image_button_{scene_number}"
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

                    st.rerun()

                else:

                    st.error(
                        f"❌ Image Error: {error}"
                    )


            # ==========================================
            # AI MOTION VIDEO BUTTON
            # ==========================================

            if scene_number in st.session_state.generated_images:

                if st.button(
                    f"🎬 Scene {scene_number} کو AI Animate کریں",
                    key=f"ai_video_button_{scene_number}"
                ):

                    with st.spinner(
                        "🤖 Wan 2.2 AI حقیقی movement بنا رہا ہے... "
                        "اس میں کچھ وقت لگ سکتا ہے۔"
                    ):

                        video_path, error = create_ai_video(
                            st.session_state.generated_images[
                                scene_number
                            ],
                            item["animation_prompt"],
                            scene_number
                        )


                    if video_path is not None:

                        st.session_state.video_files[
                            scene_number
                        ] = video_path

                        st.success(
                            "✅ AI animated video تیار ہے!"
                        )

                    else:

                        st.error(
                            f"❌ AI Video Error: {error}"
                        )


            # ==========================================
            # SHOW VIDEO
            # ==========================================

            if scene_number in st.session_state.video_files:

                video_path = (
                    st.session_state.video_files[
                        scene_number
                    ]
                )

                st.video(video_path)

                with open(
                    video_path,
                    "rb"
                ) as video_file:

                    st.download_button(
                        "⬇️ MP4 Download کریں",
                        video_file,
                        file_name=(
                            f"scene_{scene_number}_animated.mp4"
                        ),
                        mime="video/mp4",
                        key=(
                            f"download_button_{scene_number}"
                        )
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
    )
