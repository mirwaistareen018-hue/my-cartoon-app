import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave
import re

st.set_page_config(
    page_title="AI Cartoon Movie Generator",
    layout="wide",
)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

default_state = {
    "scenes": [],
    "generated_images": {},
    "video_files": {},
    "final_videos": {},
    "full_movie_path": None,
    "project_created": False,
}

for key, default in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = default

HF_TOKEN = st.secrets.get("HF_TOKEN", "")


# ---------------------------------------------------------
# IMAGE GENERATION
# ---------------------------------------------------------

def generate_image(prompt, scene_number):
    if not HF_TOKEN:
        return None, "HF_TOKEN نہیں ملا۔"

    try:
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell",
            token=HF_TOKEN,
            provider="auto",
        )

        image = client.text_to_image(prompt)

        os.makedirs("images", exist_ok=True)

        path = f"images/scene_{scene_number}.png"
        image.save(path)

        return path, None

    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------
# AI IMAGE TO VIDEO
# ---------------------------------------------------------

def create_ai_video(
    image_path,
    motion_prompt,
    scene_number,
    clip_number=1,
):
    temp_path = None

    try:
        from gradio_client import Client, handle_file

        os.makedirs("videos", exist_ok=True)

        temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )

        temp_path = temp.name
        temp.close()

        shutil.copyfile(
            image_path,
            temp_path,
        )

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
            api_name="/generate_video",
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
                output,
            )
        else:
            return None, (
                "AI video response کا format "
                "سمجھ نہیں آیا۔"
            )

        return output, None

    except Exception as exc:
        return None, str(exc)

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ---------------------------------------------------------
# BACKGROUND MUSIC
# ---------------------------------------------------------

def create_background_music(
    style,
    duration,
    output_path,
    volume=0.18,
    track=1,
):
    patterns = {
        "Happy / Cheerful": [
            [261.63, 329.63, 392.00, 329.63],
            [293.66, 349.23, 440.00, 349.23],
            [329.63, 392.00, 493.88, 392.00],
        ],
        "Cute / Sweet": [
            [392.00, 440.00, 523.25, 440.00],
            [349.23, 392.00, 493.88, 392.00],
            [440.00, 493.88, 587.33, 493.88],
        ],
        "Farm / Nature": [
            [220.00, 261.63, 329.63, 261.63],
            [196.00, 246.94, 293.66, 246.94],
            [246.94, 293.66, 369.99, 293.66],
        ],
        "Magical / Fantasy": [
            [523.25, 659.25, 783.99, 659.25],
            [493.88, 622.25, 739.99, 622.25],
            [587.33, 739.99, 880.00, 739.99],
        ],
        "Funny Cartoon": [
            [261.63, 329.63, 277.18, 369.99],
            [293.66, 369.99, 311.13, 415.30],
            [329.63, 415.30, 349.23, 440.00],
        ],
        "Peaceful": [
            [261.63, 329.63, 392.00, 523.25],
            [293.66, 349.23, 440.00, 587.33],
            [246.94, 329.63, 392.00, 493.88],
        ],
        "Cinematic": [
            [196.00, 246.94, 293.66, 392.00],
            [220.00, 277.18, 329.63, 440.00],
            [246.94, 311.13, 369.99, 493.88],
        ],
    }

    pattern_list = patterns.get(
        style,
        patterns["Happy / Cheerful"],
    )

    pattern = pattern_list[
        (track - 1) % len(pattern_list)
    ]

    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True,
    )

    sample_rate = 22050
    beat_seconds = 0.5
    total_samples = int(
        duration * sample_rate
    )

    with wave.open(
        output_path,
        "w",
    ) as wav_file:

        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        chunk_seconds = 1
        chunk_samples = (
            sample_rate * chunk_seconds
        )

        for start in range(
            0,
            total_samples,
            chunk_samples,
        ):
            end = min(
                start + chunk_samples,
                total_samples,
            )

            frames = []

            for sample_index in range(
                start,
                end,
            ):
                time_value = (
                    sample_index / sample_rate
                )

                beat_index = int(
                    time_value / beat_seconds
                )

                note = pattern[
                    beat_index % len(pattern)
                ]

                frequency = note

                envelope = (
                    0.7
                    + 0.3
                    * math.sin(
                        2
                        * math.pi
                        * time_value
                        / 8
                    )
                )

                value = (
                    math.sin(
                        2
                        * math.pi
                        * frequency
                        * time_value
                    )
                    * volume
                    * envelope
                )

                value += (
                    0.35
                    * math.sin(
                        2
                        * math.pi
                        * frequency
                        * 2
                        * time_value
                    )
                    * volume
                )

                value = max(
                    -1.0,
                    min(1.0, value),
                )

                integer_value = int(
                    value * 32767
                )

                frames.append(
                    integer_value.to_bytes(
                        2,
                        "little",
                        signed=True,
                    )
                )

            wav_file.writeframes(
                b"".join(frames)
            )


# ---------------------------------------------------------
# MUSIC FOR SINGLE SCENE
# ---------------------------------------------------------

def add_music_to_video(
    video_path,
    style,
    scene_number,
    volume=0.18,
):
    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
        )

        video = VideoFileClip(video_path)

        duration = float(
            video.duration
        )

        os.makedirs(
            "music",
            exist_ok=True,
        )

        audio_path = (
            f"music/scene_{scene_number}.wav"
        )

        create_background_music(
            style,
            duration,
            audio_path,
            volume,
            1,
        )

        audio = AudioFileClip(
            audio_path
        )

        final_video = video.with_audio(
            audio
        )

        os.makedirs(
            "final_videos",
            exist_ok=True,
        )

        output = (
            f"final_videos/"
            f"scene_{scene_number}_music.mp4"
        )

        final_video.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        audio.close()
        video.close()
        final_video.close()

        return output, None

    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------
# STORY SPLITTER
# ---------------------------------------------------------

def split_story(story, count):
    clean = story.strip()

    if not clean:
        return []

    parts = re.split(
        r"(?<=[.!?۔])\s+|\n+",
        clean,
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if len(parts) <= count:
        return parts

    groups = []

    size = math.ceil(
        len(parts) / count
    )

    for index in range(
        0,
        len(parts),
        size,
    ):
        groups.append(
            " ".join(
                parts[
                    index:index + size
                ]
            )
        )

    return groups[:count]


# ---------------------------------------------------------
# ACTION DETECTOR
# ---------------------------------------------------------

def detect_action(text):
    lower = text.lower()

    if any(
        word in lower
        for word in [
            "fly",
            "flies",
            "flying",
            "اڑ",
            "اڑتا",
            "اڑتی",
        ]
    ):
        return (
            "the character flies smoothly "
            "through the environment"
        )

    if any(
        word in lower
        for word in [
            "stone",
            "stones",
            "pebble",
            "pebbles",
            "پتھر",
            "کنکر",
        ]
    ):
        return (
            "the character picks up small "
            "stones and drops them carefully"
        )

    if any(
        word in lower
        for word in [
            "drink",
            "drinks",
            "water",
            "پانی",
            "پیتا",
            "پیتی",
        ]
    ):
        return (
            "the character drinks water happily"
        )

    if any(
        word in lower
        for word in [
            "pot",
            "مٹکا",
            "گھڑا",
            "برتن",
        ]
    ):
        return (
            "the character walks toward "
            "the pot and looks inside"
        )

    if any(
        word in lower
        for word in [
            "run",
            "runs",
            "running",
            "دوڑ",
            "دوڑتا",
            "دوڑتی",
        ]
    ):
        return (
            "the character runs naturally "
            "through the scene"
        )

    if any(
        word in lower
        for word in [
            "walk",
            "walks",
            "walking",
            "چل",
            "چلتا",
            "چلتی",
        ]
    ):
        return (
            "the character walks naturally "
            "through the scene"
        )

    if any(
        word in lower
        for word in [
            "look",
            "looks",
            "see",
            "sees",
            "دیکھ",
            "دیکھتا",
            "دیکھتی",
        ]
    ):
        return (
            "the character looks around "
            "and reacts naturally"
        )

    if any(
        word in lower
        for word in [
            "happy",
            "happily",
            "خوش",
            "مسکرا",
            "مسکراتا",
            "مسکراتی",
        ]
    ):
        return (
            "the character becomes happy "
            "and moves with cheerful energy"
        )

    if any(
        word in lower
        for word in [
            "sad",
            "cry",
            "cries",
            "اداس",
            "روتا",
            "روتی",
        ]
    ):
        return (
            "the character shows gentle "
            "sad emotion and slow movement"
        )

    return (
        "the character moves naturally "
        "with subtle body and environmental motion"
    )


# ---------------------------------------------------------
# CHARACTER DESCRIPTION
# ---------------------------------------------------------

def character_description(story):
    lower = story.lower()

    if any(
        word in lower
        for word in [
            "crow",
            "کوا",
            "کوّا",
        ]
    ):
        return (
            "a cute friendly cartoon crow, "
            "black feathers, expressive eyes, "
            "small orange beak, "
            "consistent character design"
        )

    if any(
        word in lower
        for word in [
            "rabbit",
            "خرگوش",
        ]
    ):
        return (
            "a cute friendly cartoon rabbit, "
            "soft white fur, expressive eyes, "
            "small pink nose, "
            "consistent character design"
        )

    if any(
        word in lower
        for word in [
            "fox",
            "لومڑی",
        ]
    ):
        return (
            "a cute friendly cartoon fox, "
            "orange fur, expressive eyes, "
            "white chest, "
            "consistent character design"
        )

    return (
        "a cute colorful cartoon main character, "
        "expressive eyes, friendly appearance, "
        "consistent character design"
    )


# ---------------------------------------------------------
# SCENE PLAN
# ---------------------------------------------------------

def create_scene_plan(
    story,
    count,
):
    parts = split_story(
        story,
        count,
    )

    if not parts:
        return []

    character = character_description(
        story
    )

    plan = []

    for number, text in enumerate(
        parts,
        start=1,
    ):
        action = detect_action(text)

        image_prompt = (
            "high quality 3D cartoon movie frame, "
            + character
            + ", beautiful cinematic environment, "
            + "soft lighting, colorful family friendly "
            + "animation, scene action: "
            + text
        )

        motion_prompt = (
            action
            + ", based on this story moment: "
            + text
        )

        plan.append(
            {
                "scene": number,
                "story": text,
                "image_prompt": image_prompt,
                "motion_prompt": motion_prompt,
            }
        )

    return plan


# ---------------------------------------------------------
# COMBINE VIDEO CLIPS
# ---------------------------------------------------------

def combine_video_clips(
    video_paths,
    output_path,
    target_duration,
):
    try:
        from moviepy import (
            VideoFileClip,
            concatenate_videoclips,
        )

        if not video_paths:
            return None, (
                "کوئی video clips نہیں ملیں۔"
            )

        source_clips = []

        for path in video_paths:
            if (
                path
                and os.path.exists(path)
            ):
                source_clips.append(
                    VideoFileClip(path)
                )

        if not source_clips:
            return None, (
                "Valid video clips نہیں ملیں۔"
            )

        total_duration = sum(
            float(clip.duration)
            for clip in source_clips
        )

        if total_duration < target_duration:
            repeats = math.ceil(
                target_duration
                / total_duration
            )

            clips = (
                source_clips
                * repeats
            )
        else:
            clips = source_clips

        final_clip = concatenate_videoclips(
            clips,
            method="compose",
        )

        if (
            final_clip.duration
            > target_duration
        ):
            final_clip = (
                final_clip.subclipped(
                    0,
                    target_duration,
                )
            )

        os.makedirs(
            os.path.dirname(output_path)
            or ".",
            exist_ok=True,
        )

        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        final_clip.close()

        for clip in source_clips:
            clip.close()

        return output_path, None

    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------
# FULL MOVIE MUSIC
# ---------------------------------------------------------

def add_full_movie_music(
    video_path,
    style,
    track,
    volume,
):
    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
        )

        video = VideoFileClip(
            video_path
        )

        duration = float(
            video.duration
        )

        os.makedirs(
            "music",
            exist_ok=True,
        )

        music_path = (
            "music/full_movie_music.wav"
        )

        create_background_music(
            style,
            duration,
            music_path,
            volume,
            track,
        )

        audio = AudioFileClip(
            music_path
        )

        final_video = video.with_audio(
            audio
        )

        output = (
            "final_movie_with_music.mp4"
        )

        final_video.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        audio.close()
        video.close()
        final_video.close()

        return output, None

    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------
# FULL MOVIE BUILDER
# ---------------------------------------------------------

def build_full_movie(
    scenes,
    target_duration,
    clips_per_scene,
    music_style,
    music_track,
    music_volume,
    progress,
    status,
):
    os.makedirs(
        "images",
        exist_ok=True,
    )

    os.makedirs(
        "videos",
        exist_ok=True,
    )

    all_clips = []

    total_steps = max(
        1,
        len(scenes)
        + len(scenes)
        * clips_per_scene
        + 2,
    )

    completed = 0

    for scene in scenes:
        number = scene["scene"]

        status.write(
            f"🖼️ Scene {number}: "
            "image بن رہی ہے..."
        )

        image_path = (
            st.session_state
            .generated_images
            .get(number)
        )

        if (
            not image_path
            or not os.path.exists(
                image_path
            )
        ):
            image_path, error = (
                generate_image(
                    scene["image_prompt"],
                    number,
                
