import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="AI Cartoon Video Studio",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Cartoon Video Studio")


# =========================================================
# SESSION STATE
# =========================================================

if "scenes" not in st.session_state:
    st.session_state.scenes = []

if "generated_images" not in st.session_state:
    st.session_state.generated_images = {}

if "video_files" not in st.session_state:
    st.session_state.video_files = {}

if "final_videos" not in st.session_state:
    st.session_state.final_videos = {}

if "project_created" not in st.session_state:
    st.session_state.project_created = False


# =========================================================
# IMAGE GENERATION
# =========================================================

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


# =========================================================
# AI IMAGE TO VIDEO
# =========================================================

def create_ai_video(image, motion_prompt, scene_number):

    try:

        from gradio_client import Client, handle_file

        os.makedirs("videos", exist_ok=True)

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        )

        temp_image_path = temp_file.name
        temp_file.close()

        image.save(temp_image_path)

        client = Client(
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
        )

        prompt = (
            motion_prompt
            + ", smooth natural movement, "
            + "natural body movement, "
            + "natural head movement, "
            + "gentle environmental movement, "
            + "cinematic camera movement, "
            + "stable character appearance"
        )

        negative_prompt = (
            "static image, frozen frame, "
            + "no movement, blurry, distorted, "
            + "deformed character, extra limbs, "
            + "flickering, unstable face, "
            + "warped body, bad anatomy"
        )

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

        if isinstance(result, (list, tuple)):
            generated_video = result[0]
        else:
            generated_video = result

        if not generated_video:
            return None, "AI نے video file واپس نہیں کی۔"

        video_path = (
            f"videos/scene_{scene_number}_ai.mp4"
        )

        if isinstance(generated_video, str):

            shutil.copyfile(
                generated_video,
                video_path
            )

        else:

            return None, "AI video response سمجھ نہیں آیا۔"

        try:
            os.remove(temp_image_path)
        except Exception:
            pass

        return video_path, None

    except Exception as e:

        return None, str(e)


# =========================================================
# BACKGROUND MUSIC
# =========================================================

def create_background_music(
    style,
    duration,
    output_path,
    volume
):

    sample_rate = 22050
    total_samples = int(duration * sample_rate)

    music_styles = {

        "😊 Happy / Cheerful": {
            "notes": [261.63, 329.63, 392.00, 523.25],
            "tempo": 0.28
        },

        "🌸 Cute / Sweet": {
            "notes": [261.63, 293.66, 329.63, 392.00],
            "tempo": 0.38
        },

        "🌾 Farm / Nature": {
            "notes": [220.00, 261.63, 329.63, 392.00],
            "tempo": 0.55
        },

        "✨ Magical / Fantasy": {
            "notes": [261.63, 349.23, 440.00, 523.25],
            "tempo": 0.48
        },

        "😂 Funny Cartoon": {
            "notes": [293.66, 369.99, 440.00, 587.33],
            "tempo": 0.22
        },

        "😌 Peaceful": {
            "notes": [220.00, 261.63, 329.63, 392.00],
            "tempo": 0.75
        },

        "🎬 Cinematic": {
            "notes": [196.00, 246.94, 293.66, 392.00],
            "tempo": 0.65
        }
    }

    selected = music_styles.get(
        style,
        music_styles["😊 Happy / Cheerful"]
    )

    notes = selected["notes"]
    tempo = selected["tempo"]

    frames = []

    for i in range(total_samples):

        current_time = i / sample_rate

        note_index = int(
            current_time / tempo
        ) % len(notes)

        frequency = notes[note_index]

        melody = math.sin(
            2 * math.pi * frequency * current_time
        )

        harmonic = 0.30 * math.sin(
            2 * math.pi * frequency * 2 * current_time
        )

        bass = 0.12 * math.sin(
            2 * math.pi * (frequency / 2) * current_time
        )

        fade_in = min(
            1.0,
            current_time / 0.8
        )

        remaining = duration - current_time

        fade_out = min(
            1.0,
            remaining / 1.2
        )

        envelope = min(
            fade_in,
            fade_out
        )

        sample = (
            melody
            + harmonic
            + bass
        )

        sample = sample * volume * envelope

        sample = max(
            -1.0,
            min(1.0, sample)
        )

        integer_sample = int(
            sample * 32767
        )

        frames.append(
            integer_sample.to_bytes(
                2,
                byteorder="little",
                signed=True
            )
        )

    with wave.open(
        output_path,
        "wb"
    ) as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        wav.writeframes(
            b"".join(frames)
        )

    return output_path


# =========================================================
# ADD MUSIC TO VIDEO
# =========================================================

def add_music_to_video(
    video_path,
    style,
    scene_number,
    volume
):

    try:

        from moviepy import (
            VideoFileClip,
            AudioFileClip
        )

        os.makedirs(
            "music",
            exist_ok=True
        )

        os.makedirs(
            "final_videos",
            exist_ok=True
        )

        music_path = (
            f"music/scene_{scene_number}.wav"
        )

        final_path = (
            f"final_videos/"
            f"scene_{scene_number}_final.mp4"
        )

        video = VideoFileClip(video_path)

        duration = video.duration

        create_background_music(
            style,
            duration,
            music_path,
            volume
        )

        audio = AudioFileClip(music_path)

        final_video = video.with_audio(audio)

        final_video.write_videofile(
            final_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None
        )

        final_video.close()
        audio.close()
        video.close()

        return final_path, None

    except Exception as e:

        return None, str(e)


# =========================================================
# LANGUAGE
# =========================================================

language = st.selectbox(
    "زبان / Language",
    ["اردو", "English"]
)


# =========================================================
# STORY INPUT
# =========================================================

if language == "اردو":

    st.header("📝 اپنی کہانی لکھیں")

    script = st.text_area(
        "کہانی:",
        placeholder=(
            "مثال: ایک پیاری مرغی "
            "اپنے بچوں کے ساتھ کھیت میں جاتی ہے۔"
        ),
        height=180
    )

    scene_count = st.slider(
        "کتنے Scenes؟",
        1,
        10,
        5
    )

    create_button_text = (
        "🎬 Cartoon Project بنائیں"
    )

else:

    st.header("📝 Write Your Story")

    script = st.text_area(
        "Story:",
        placeholder=(
            "Example: A cute hen goes "
            "to the farm with her chicks."
        ),
        height=180
    )

    scene_count = st.slider(
        "Number of Scenes",
        1,
        10,
        5
    )

    create_button_text = (
        "🎬 Create Cartoon Project"
    )


# =========================================================
# MUSIC SETTINGS
# =========================================================

st.header("🎵 Background Music")

music_style = st.selectbox(
    "Music کی قسم منتخب کریں:",
    [
        "😊 Happy / Cheerful",
        "🌸 Cute / Sweet",
        "🌾 Farm / Nature",
        "✨ Magical / Fantasy",
        "😂 Funny Cartoon",
        "😌 Peaceful",
        "🎬 Cinematic"
    ]
)

music_volume = st.slider(
    "🎵 Music Volume",
    0.05,
    0.40,
    0.18,
    0.01
)

st.info(
    "🎵 صرف background instrumental music ہوگا۔ "
    "کوئی انسان کی آواز یا dialogue نہیں ہوگا۔"
)


# =========================================================
# SCENE PLANNER
# =========================================================

def create_scene_plan(
    story,
    count,
    language
):

    scenes = []

    for i in range(1, count + 1):

        if language == "اردو":

            scenes.append({
                "scene": i,
                "story": f"{story} — حصہ {i}",
                "character": "پیاری مرغی اور اس کا چھوٹا بچہ",

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
                    "The mother hen gently moves "
                    "her head and body, "
                    "the little chick walks naturally, "
                    "their feathers move gently, "
                    "grass and plants move in the breeze, "
                    "clouds move slowly, "
                    "gentle cinematic camera movement"
                )
            })

        else:

            scenes.append({
                "scene": i,
                "story": f"{story} — Part {i}",
                "character": "Cute mother hen and her little chick",

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
                    "The mother hen gently moves "
                    "her head and body, "
                    "the little chick walks naturally, "
                    "their feathers move gently, "
                    "grass and plants move in the breeze, "
                    "clouds move slowly, "
                    "gentle cinematic camera movement"
                )
            })

    return scenes


# =========================================================
# CREATE PROJECT
# =========================================================

if st.button(
    create_button_text,
    type="primary"
):

    if not script.strip():

        st.warning(
            "پہلے اپنی کہانی لکھیں۔"
        )

    else:

        st.session_state.scenes = create_scene_plan(
            script,
            scene_count,
            language
        )

        st.session_state.generated_images = {}
        st.session_state.video_files = {}
        st.session_state.final_videos = {}
        st.session_state.project_created = True

        st.success(
            "✅ Cartoon Project تیار ہے!"
        )


# =========================================================
# PROJECT
# =========================================================

if st.session_state.project_created:

    st.header("🎭 Character Bible")

    st.write(
        "مرکزی کردار: پیاری مرغی اور اس کا بچہ۔ "
        "ہم تمام Scenes میں ان کی شکل کو مستقل "
        "رکھنے کی کوشش کریں گے۔"
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


            # =================================================
            # IMAGE
            # =================================================

            if scene_number in st.session_state.generated_images:

                st.image(
                    st.session_state.generated_images[
                        scene_number
                    ],
                    caption=f"Scene {scene_number}"
                )


            # =================================================
            # GENERATE IMAGE
            # =================================================

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


            # =================================================
            # AI ANIMATION
            # =================================================

            if scene_number in st.session_state.generated_images:

                if st.button(
                    f"🎬 Scene {scene_number} کو AI Animate کریں",
                    key=f"animate_button_{scene_number}"
                ):

                    with st.spinner(
                        "🤖 AI movement بنا رہا ہے..."
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


            # =================================================
            # SHOW ANIMATED VIDEO
            # =================================================

            if scene_number in st.session_state.video_files:

                video_path = (
                    st.session_state.video_files[
                        scene_number
                    ]
                )

                st.subheader(
                    "🤖 AI Animated Video"
                )

                st.video(video_path)


                # =================================================
                # MUSIC BUTTON
                # =================================================

                if st.button(
                    f"🎵 Scene {scene_number} میں Music لگائیں",
                    key=f"music_button_{scene_number}"
                ):

                    with st.spinner(
                        "🎵 خوبصورت background music تیار ہو رہا ہے..."
                    ):

                        final_path, error = add_music_to_video(
                            video_path,
                            music_style,
                            scene_number,
                            music_volume
                        )

                    if final_path is not None:

                        st.session_state.final_videos[
                            scene_number
                        ] = final_path

                        st.success(
                            "🎉 Music کے ساتھ Final Video تیار ہے!"
                        )

                    else:

                        st.error(
                            f"❌ Music Error: {error}"
                        )


            # =================================================
            # FINAL VIDEO
            # =================================================

            if scene_number in st.session_state.final_videos:

                final_path = (
                    st.session_state.final_videos[
                        scene_number
                    ]
                )

                st.subheader(
                    "🎞️ Final Video"
                )

                st.video(final_path)

                with open(
                    final_path,
                    "rb"
                ) as final_file:

                    st.download_button(
                        "⬇️ Final MP4 Download کریں",
                        final_file,
                        file_name=(
                            f"scene_{scene_number}_final.mp4"
                        ),
                        mime="video/mp4",
                        key=f"download_button_{scene_number}"
                    )


# =========================================================
# PIPELINE
# =========================================================

st.divider()

st.header(
    "🚧 AI Generation Pipeline"
)

st.write(
    "📝 Story → 🎬 Scenes → 🖼️ AI Images → "
    "🤖 AI Motion → 🎵 Background Music → "
    "🎞️ Final MP4"
        )
