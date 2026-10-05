import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave

st.set_page_config(
    page_title="AI Cartoon Movie Studio",
    page_icon="🎬",
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "scenes": [],
    "generated_images": {},
    "video_files": {},
    "final_videos": {},
    "project_created": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        if isinstance(value, dict):
            st.session_state[key] = {}
        elif isinstance(value, list):
            st.session_state[key] = []
        else:
            st.session_state[key] = value


# =========================================================
# AI IMAGE GENERATION
# =========================================================

def generate_image(prompt):

    token = st.secrets.get("HF_TOKEN")

    if not token:
        return None, "HF_TOKEN نہیں ملا۔ Streamlit Secrets میں HF_TOKEN چیک کریں۔"

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

    except Exception as exc:

        return None, str(exc)


# =========================================================
# AI IMAGE TO VIDEO
# =========================================================

def create_ai_video(
    image,
    motion_prompt,
    scene_number,
    clip_number=1
):

    try:

        from gradio_client import Client, handle_file

        os.makedirs(
            "videos",
            exist_ok=True
        )

        temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        )

        temp_path = temp.name
        temp.close()

        image.save(temp_path)

        client = Client(
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
        )

        prompt = (
            motion_prompt
            + ", smooth natural movement, "
            + "natural body movement, "
            + "natural environmental movement, "
            + "cinematic camera movement, "
            + "stable character appearance"
        )

        negative_prompt = (
            "static image, frozen frame, no movement, "
            + "blurry, distorted, deformed character, "
            + "extra limbs, flickering, unstable face, "
            + "warped body, bad anatomy"
        )

        result = client.predict(
            handle_file(temp_path),
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
            generated = result[0]
        else:
            generated = result

        if not generated:
            return None, "AI نے video file واپس نہیں کی۔"

        output = (
            f"videos/scene_{scene_number}"
            f"_clip_{clip_number}.mp4"
        )

        if isinstance(generated, str):

            shutil.copyfile(
                generated,
                output
            )

        else:

            return None, (
                "AI video response کا format "
                "سمجھ نہیں آیا۔"
            )

        try:
            os.remove(temp_path)
        except Exception:
            pass

        return output, None

    except Exception as exc:

        return None, str(exc)


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

    total_samples = max(
        1,
        int(duration * sample_rate)
    )

    music_styles = {

        "😊 Happy / Cheerful": (
            [261.63, 329.63, 392.00, 523.25],
            0.28
        ),

        "🌸 Cute / Sweet": (
            [261.63, 293.66, 329.63, 392.00],
            0.38
        ),

        "🌾 Farm / Nature": (
            [220.00, 261.63, 329.63, 392.00],
            0.55
        ),

        "✨ Magical / Fantasy": (
            [261.63, 349.23, 440.00, 523.25],
            0.48
        ),

        "😂 Funny Cartoon": (
            [293.66, 369.99, 440.00, 587.33],
            0.22
        ),

        "😌 Peaceful": (
            [220.00, 261.63, 329.63, 392.00],
            0.75
        ),

        "🎬 Cinematic": (
            [196.00, 246.94, 293.66, 392.00],
            0.65
        )
    }

    notes, tempo = music_styles.get(
        style,
        music_styles["😊 Happy / Cheerful"]
    )

    frames = []

    for i in range(total_samples):

        current_time = i / sample_rate

        note_index = (
            int(current_time / tempo)
            % len(notes)
        )

        frequency = notes[note_index]

        melody = math.sin(
            2 * math.pi
            * frequency
            * current_time
        )

        harmony = (
            0.30
            * math.sin(
                2 * math.pi
                * frequency
                * 2
                * current_time
            )
        )

        bass = (
            0.12
            * math.sin(
                2 * math.pi
                * (frequency / 2)
                * current_time
            )
        )

        fade_in = min(
            1.0,
            current_time / 0.8
        )

        remaining = (
            duration - current_time
        )

        fade_out = min(
            1.0,
            max(
                0.0,
                remaining / 1.2
            )
        )

        envelope = min(
            fade_in,
            fade_out
        )

        sample = (
            melody
            + harmony
            + bass
        )

        sample = (
            sample
            * volume
            * envelope
        )

        sample = max(
            -1.0,
            min(
                1.0,
                sample
            )
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

        video = VideoFileClip(
            video_path
        )

        duration = video.duration

        create_background_music(
            style,
            duration,
            music_path,
            volume
        )

        audio = AudioFileClip(
            music_path
        )

        final_video = video.with_audio(
            audio
        )

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

    except Exception as exc:

        return None, str(exc)


# =========================================================
# STORY PLAN
# =========================================================

def create_scene_plan(
    story,
    count,
    language
):

    scenes = []

    for i in range(
        1,
        count + 1
    ):

        if language == "اردو":

            story_text = (
                f"{story} — حصہ {i}"
            )

            character = (
                "کہانی کے اصل کردار"
            )

            image_prompt = (
                "2D colorful children's cartoon, "
                "friendly expressive characters, "
                "consistent character design, "
                "beautiful cinematic environment, "
                "child-friendly animation style, "
                f"story: {story}, "
                f"scene {i}"
            )

            animation_prompt = (
                "Characters perform the story action "
                "naturally; walking, stopping, looking, "
                "turning, interacting with the environment "
                "when appropriate; gentle cinematic "
                "camera movement."
            )

        else:

            story_text = (
                f"{story} — Part {i}"
            )

            character = (
                "Main story characters"
            )

            image_prompt = (
                "2D colorful children's cartoon, "
                "friendly expressive characters, "
                "consistent character design, "
                "beautiful cinematic environment, "
                "child-friendly animation style, "
                f"story: {story}, "
                f"scene {i}"
            )

            animation_prompt = (
                "Characters perform the story action "
                "naturally; walking, stopping, looking, "
                "turning, interacting with the environment "
                "when appropriate; gentle cinematic "
                "camera movement."
            )

        scenes.append({
            "scene": i,
            "story": story_text,
            "character": character,
            "image_prompt": image_prompt,
            "animation_prompt": animation_prompt
        })

    return scenes


# =========================================================
# MAIN UI
# =========================================================

st.title(
    "🎬 AI Cartoon Movie Studio"
)

language = st.selectbox(
    "زبان / Language",
    [
        "اردو",
        "English"
    ]
)


# =========================================================
# STORY
# =========================================================

if language == "اردو":

    st.header(
        "📝 اپنی مکمل کہانی لکھیں"
    )

    script = st.text_area(
        "کہانی یہاں paste کریں:",
        placeholder=(
            "مثال: ایک دفعہ ایک جنگل میں "
            "ایک پیاسا کوا رہتا تھا..."
        ),
        height=220
    )

else:

    st.header(
        "📝 Write Your Complete Story"
    )

    script = st.text_area(
        "Paste your story here:",
        placeholder=(
            "Example: Once there was "
            "a thirsty crow in a forest..."
        ),
        height=220
    )


# =========================================================
# DURATION
# =========================================================

st.header(
    "⏱️ Video Duration"
)

duration_minutes = st.selectbox(
    "Cartoon movie کتنی لمبی ہو؟",
    [
        2,
        3,
        4,
        5
    ],
    index=0
)

duration_seconds = (
    duration_minutes * 60
)

scene_count = (
    duration_minutes * 4
)

st.info(
    f"🎬 منتخب duration: "
    f"{duration_minutes} منٹ "
    f"({duration_seconds} سیکنڈ) | "
    f"تقریباً {scene_count} story scenes"
)


# =========================================================
# MUSIC
# =========================================================

st.header(
    "🎵 Background Music"
)

music_style = st.selectbox(
    "اپنی music style منتخب کریں:",
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
    "Music Volume",
    0.05,
    0.40,
    0.18,
    0.01
)

st.caption(
    "🎵 یہ instrumental background music ہے؛ "
    "اس میں human singing نہیں ہے۔"
)


# =========================================================
# CREATE PROJECT
# =========================================================

if language == "اردو":

    create_button_text = (
        "🎬 Cartoon Movie Project بنائیں"
    )

else:

    create_button_text = (
        "🎬 Create Cartoon Movie Project"
    )


if st.button(
    create_button_text,
    type="primary"
):

    if not script.strip():

        st.warning(
            "پہلے مکمل کہانی paste کریں۔"
        )

    else:

        st.session_state.scenes = (
            create_scene_plan(
                script,
                scene_count,
                language
            )
        )

        st.session_state.generated_images = {}
        st.session_state.video_files = {}
        st.session_state.final_videos = {}

        st.session_state.project_created = True

        st.success(
            "✅ Story کو movie scenes میں تقسیم کر دیا گیا ہے!"
        )


# =========================================================
# PROJECT
# =========================================================

if st.session_state.project_created:

    st.divider()

    st.header(
        "🎬 Story Scenes"
    )

    for item in st.session_state.scenes:

        scene_number = item["scene"]

        with st.expander(
            f"🎬 Scene {scene_number}",
            expanded=(
                scene_number == 1
            )
        ):

            st.write(
                f"📖 **Story:** "
                f"{item['story']}"
            )

            st.write(
                f"🎭 **Character:** "
                f"{item['character']}"
            )

            st.write(
                f"🎥 **Action:** "
                f"{item['animation_prompt']}"
            )


            # =================================================
            # IMAGE
            # =================================================

            if (
                scene_number
                in st.session_state.generated_images
            ):

                st.image(
                    st.session_state.generated_images[
                        scene_number
                    ],
                    caption=(
                        f"Scene {scene_number}"
                    )
                )


            # =================================================
            # GENERATE IMAGE
            # =================================================

            if st.button(
                f"🖼️ Scene {scene_number} کی تصویر بنائیں",
                key=f"image_{scene_number}"
            ):

                with st.spinner(
                    "🎨 AI تصویر بنا رہا ہے..."
                ):

                    image, error = (
                        generate_image(
                            item["image_prompt"]
                        )
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
            # AI MOTION
            # =================================================

            if (
                scene_number
                in st.session_state.generated_images
            ):

                if st.button(
                    f"🎥 Scene {scene_number} کو Animate کریں",
                    key=f"animate_{scene_number}"
                ):

                    with st.spinner(
                        "🤖 AI scene movement بنا رہا ہے..."
                    ):

                        video_path, error = (
                            create_ai_video(
                                st.session_state.generated_images[
                                    scene_number
                                ],
                                item["animation_prompt"],
                                scene_number
                            )
                        )

                    if video_path is not None:

                        st.session_state.video_files[
                            scene_number
                        ] = video_path

                        st.success(
                            "✅ Animated video تیار ہے!"
                        )

                    else:

                        st.error(
                            f"❌ AI Video Error: {error}"
                        )


            # =================================================
            # SHOW VIDEO
            # =================================================

            if (
                scene_number
                in st.session_state.video_files
            ):

                video_path = (
                    st.session_state.video_files[
                        scene_number
                    ]
                )

                st.video(
                    video_path
                )


                # =================================================
                # MUSIC
                # =================================================

                if st.button(
                    f"🎵 Scene {scene_number} میں Music لگائیں",
                    key=f"music_{scene_number}"
                ):

                    with st.spinner(
                        "🎵 Background music تیار ہو رہا ہے..."
                    ):

                        final_path, error = (
                            add_music_to_video(
                                video_path,
                                music_style,
                                scene_number,
                                music_volume
                            )
                        )

                    if final_path is not None:

                        st.session_state.final_videos[
                            scene_number
                        ] = final_path

                        st.success(
                            "🎉 Music کے ساتھ final scene تیار ہے!"
                        )

                    else:

                        st.error(
                            f"❌ Music Error: {error}"
                        )


            # =================================================
            # FINAL SCENE
            # =================================================

            if (
                scene_number
                in st.session_state.final_videos
            ):

                final_path = (
                    st.session_state.final_videos[
                        scene_number
                    ]
                )

                st.subheader(
                    "🎞️ Final Scene"
                )

                st.video(
                    final_path
                )

                with open(
                    final_path,
                    "rb"
                ) as file:

                    st.download_button(
                        "⬇️ MP4 Download کریں",
                        file,
                        file_name=(
                            f"scene_{scene_number}_final.mp4"
                        ),
                        mime="video/mp4",
                        key=(
                            f"download_{scene_number}"
                        )
                    )


# =========================================================
# PIPELINE
# =====================
