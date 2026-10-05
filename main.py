import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave
import re
import json
import time
import numpy as np

st.set_page_config(page_title="AI Cartoon Movie Generator", layout="wide")

PROJECT_DIR = "cartoon_project"
IMAGES_DIR = os.path.join(PROJECT_DIR, "images")
VIDEOS_DIR = os.path.join(PROJECT_DIR, "videos")
MUSIC_DIR = os.path.join(PROJECT_DIR, "music")
STATE_FILE = os.path.join(PROJECT_DIR, "project_state.json")

for directory in [PROJECT_DIR, IMAGES_DIR, VIDEOS_DIR, MUSIC_DIR]:
    os.makedirs(directory, exist_ok=True)

for key, default in {
    "scenes": [],
    "images": {},
    "videos": {},
    "full_movie": None,
    "project_state": {},
    "engine_message": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

HF_TOKEN = st.secrets.get("HF_TOKEN", "")


def safe_error(exc):
    text = str(exc).strip()
    if not text:
        text = exc.__class__.__name__
    return text[:2000]


def load_project():
    if not os.path.exists(STATE_FILE):
        return False

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        st.session_state.scenes = data.get("scenes", [])
        st.session_state.images = data.get("images", {})
        st.session_state.videos = data.get("videos", {})
        st.session_state.full_movie = data.get("full_movie")
        st.session_state.project_state = data
        return True

    except Exception:
        return False


def save_project(extra=None):
    data = {
        "version": 2,
        "updated_at": time.time(),
        "scenes": st.session_state.scenes,
        "images": st.session_state.images,
        "videos": st.session_state.videos,
        "full_movie": st.session_state.full_movie,
    }

    if extra:
        data.update(extra)

    temp_file = STATE_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temp_file, STATE_FILE)
    st.session_state.project_state = data


def existing_file(path):
    return bool(
        path
        and isinstance(path, str)
        and os.path.exists(path)
    )


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

        path = os.path.join(
            IMAGES_DIR,
            f"scene_{scene_number}.png",
        )

        image.save(path)

        return path, None

    except Exception as exc:
        return None, safe_error(exc)


# =========================================================
# VIDEO ENGINE LAYER
# =========================================================

def local_video_engine_available():
    return False


def create_local_video(*args, **kwargs):
    return (
        None,
        "اس computer پر ابھی کوئی compatible local AI video engine دستیاب نہیں۔",
    )


def create_remote_video(
    image_path,
    motion_prompt,
    scene_number,
    clip_number=1,
):
    temp_path = None

    try:
        from gradio_client import Client, handle_file

        if not existing_file(image_path):
            return None, "Image file نہیں ملی۔"

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
            "static image, frozen frame, blurry, distorted, "
            + "deformed character, extra limbs, flickering, "
            + "unstable face, warped body, bad anatomy"
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

        generated = (
            result[0]
            if isinstance(result, (list, tuple))
            else result
        )

        if not generated or not isinstance(generated, str):
            return None, "AI نے video file واپس نہیں کی۔"

        output = os.path.join(
            VIDEOS_DIR,
            f"scene_{scene_number}_clip_{clip_number}.mp4",
        )

        shutil.copyfile(
            generated,
            output,
        )

        return output, None

    except Exception as exc:
        return None, safe_error(exc)

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def create_ai_video(
    image_path,
    motion_prompt,
    scene_number,
    clip_number=1,
):
    if local_video_engine_available():
        path, error = create_local_video(
            image_path,
            motion_prompt,
            scene_number,
            clip_number,
        )

        if path:
            return path, None

    return create_remote_video(
        image_path,
        motion_prompt,
        scene_number,
        clip_number,
    )


# =========================================================
# MUSIC ENGINE
# =========================================================

def create_music(
    style,
    duration,
    output_path,
    volume=0.18,
    track=1,
):
    patterns = {
        "Happy / Cheerful": [
            261.63,
            329.63,
            392.00,
            523.25,
        ],
        "Cute / Sweet": [
            392.00,
            440.00,
            523.25,
            587.33,
        ],
        "Farm / Nature": [
            220.00,
            261.63,
            329.63,
            392.00,
        ],
        "Magical / Fantasy": [
            523.25,
            659.25,
            783.99,
            1046.50,
        ],
        "Funny Cartoon": [
            261.63,
            329.63,
            277.18,
            369.99,
        ],
        "Peaceful": [
            261.63,
            329.63,
            392.00,
            523.25,
        ],
        "Cinematic": [
            196.00,
            246.94,
            293.66,
            392.00,
        ],
    }

    notes = list(
        patterns.get(
            style,
            patterns["Happy / Cheerful"],
        )
    )

    if track == 2:
        notes = notes[1:] + notes[:1]

    elif track == 3:
        notes = list(reversed(notes))

    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True,
    )

    sample_rate = 22050
    duration = max(
        0.0,
        float(duration),
    )

    total_samples = int(
        duration * sample_rate
    )

    if total_samples <= 0:
        return

    t = np.linspace(
        0,
        duration,
        total_samples,
        endpoint=False,
    )

    freq_pattern = np.array(
        notes,
        dtype=float,
    )

    freq_indices = (
        (t * 2).astype(int)
        % len(freq_pattern)
    )

    freqs = freq_pattern[
        freq_indices
    ]

    wave_data = (
        np.sin(
            2 * np.pi * freqs * t
        )
        * float(volume)
    )

    wave_data = np.clip(
        wave_data,
        -1.0,
        1.0,
    )

    wave_data = (
        wave_data * 32767
    ).astype(np.int16)

    with wave.open(
        output_path,
        "wb",
    ) as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(
            wave_data.tobytes()
        )


# =========================================================
# STORY ENGINE
# =========================================================

def split_story(story, count):
    parts = re.split(
        r"(?<=[.!?۔])\s+|\n+",
        story.strip(),
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if not parts:
        return []

    if len(parts) <= count:
        return parts

    size = math.ceil(
        len(parts) / count
    )

    return [
        " ".join(
            parts[i:i + size]
        )
        for i in range(
            0,
            len(parts),
            size,
        )
    ][:count]


def character_description(story):
    text = story.lower()

    if (
        "crow" in text
        or "کوا" in text
    ):
        return (
            "a cute cartoon crow with black feathers, "
            "expressive eyes and orange beak"
        )

    if (
        "rabbit" in text
        or "خرگوش" in text
    ):
        return (
            "a cute cartoon rabbit with soft white fur "
            "and expressive eyes"
        )

    if (
        "fox" in text
        or "لومڑی" in text
    ):
        return (
            "a cute cartoon fox with orange fur "
            "and expressive eyes"
        )

    return (
        "a cute colorful cartoon main character "
        "with expressive eyes"
    )


def detect_action(text):
    lower = text.lower()

    if any(
        word in lower
        for word in [
            "fly",
            "flies",
            "اڑ",
            "اڑتا",
            "اڑتی",
        ]
    ):
        return (
            "flies smoothly through the scene"
        )

    if any(
        word in lower
        for word in [
            "stone",
            "stones",
            "پتھر",
        ]
    ):
        return (
            "picks up small stones "
            "and drops them carefully"
        )

    if any(
        word in lower
        for word in [
            "water",
            "پانی",
        ]
    ):
        return (
            "moves toward the water "
            "and drinks happily"
        )

    if any(
        word in lower
        for word in [
            "pot",
            "مٹکا",
            "گھڑا",
        ]
    ):
        return (
            "walks toward the pot "
            "and looks inside"
        )

    if any(
        word in lower
        for word in [
            "drink",
            "drinks",
            "پیتا",
            "پیتی",
            "پینا",
        ]
    ):
        return "drinks happily"

    if any(
        word in lower
        for word in [
            "run",
            "runs",
            "دوڑ",
            "دوڑتا",
            "دوڑتی",
        ]
    ):
        return (
            "runs naturally through the scene"
        )

    if any(
        word in lower
        for word in [
            "walk",
            "walks",
            "چل",
            "چلتا",
            "چلتی",
        ]
    ):
        return (
            "walks naturally through the scene"
        )

    return (
        "moves naturally "
        "with subtle cinematic motion"
    )


def make_scene_plan(story, count):
    pieces = split_story(
        story,
        count,
    )

    character = character_description(
        story
    )

    scenes = []

    for number, text in enumerate(
        pieces,
        1,
    ):
        scenes.append(
            {
                "number": number,
                "story": text,
                "image_prompt": (
                    "high quality 3D cartoon movie frame, "
                    + character
                    + ", beautiful cinematic environment, "
                    + "colorful family friendly animation, "
                    + "consistent character design, "
                    + "story moment: "
                    + text
                ),
                "motion_prompt": (
                    detect_action(text)
                    + ", story moment: "
                    + text
                ),
            }
        )

    return scenes


# =========================================================
# MOVIE EDITOR
# =========================================================

def combine_clips(
    paths,
    output_path,
    target_duration,
):
    clips = []
    final = None

    try:
        from moviepy import (
            VideoFileClip,
            concatenate_videoclips,
        )

        valid = [
            path
            for path in paths
            if existing_file(path)
        ]

        if not valid:
            return (
                None,
                "کوئی video clips نہیں ملیں۔",
            )

        clips = [
            VideoFileClip(path)
            for path in valid
        ]

        total = sum(
            float(
                clip.duration or 0
            )
            for clip in clips
        )

        if total <= 0:
            return (
                None,
                "Video duration صفر ہے۔",
            )

        target_duration = max(
            1.0,
            float(target_duration),
        )

        repeats = max(
            1,
            math.ceil(
                target_duration / total
            ),
        )

        final = concatenate_videoclips(
            clips * repeats,
            method="compose",
        )

        if (
            final.duration
            > target_duration
        ):
            final = final.subclipped(
                0,
                target_duration,
            )

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        return output_path, None

    except Exception as exc:
        return None, safe_error(exc)

    finally:
        if final is not None:
            try:
                final.close()
            except Exception:
                pass

        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass


def add_full_music(
    video_path,
    style,
    track,
    volume,
):
    video = None
    audio = None
    final = None

    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
        )

        if not existing_file(
            video_path
        ):
            return (
                None,
                "Silent movie file نہیں ملی۔",
            )

        video = VideoFileClip(
            video_path
        )

        music_path = os.path.join(
            MUSIC_DIR,
            "full_movie.wav",
        )

        create_music(
            style,
            float(video.duration),
            music_path,
            volume,
            track,
        )

        audio = AudioFileClip(
            music_path
        )

        final = video.with_audio(
            audio
        )

        output = os.path.join(
            PROJECT_DIR,
            "final_cartoon_movie.mp4",
        )

        final.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        return output, None

    except Exception as exc:
        return None, safe_error(exc)

    finally:
        if final is not None:
            try:
                final.close()
            except Exception:
                pass

        if audio is not None:
            try:
                audio.close()
            except Exception:
                pass

        if video is not None:
            try:
                video.close()
            except Exception:
                pass


# =========================================================
# RESUMABLE MOVIE BUILDER
# =========================================================

def build_movie(
    scenes,
    duration_minutes,
    clips_per_scene,
    music_style,
    music_track,
    music_volume,
    progress,
    status,
):
    all_clips = []

    total_tasks = (
        len(scenes)
        * (1 + clips_per_scene)
        + 2
    )

    completed = 0

    for scene in scenes:
        number = scene["number"]

        status.write(
            f"🖼️ Scene {number}: image check..."
        )

        image_path = (
            st.session_state.images.get(
                str(number)
            )
        )

        if not existing_file(
            image_path
        ):
            image_path = (
                st.session_state.images.get(
                    number
                )
            )

        if not existing_file(
            image_path
        ):
            status.write(
                f"🖼️ Scene {number}: AI image..."
            )

            image_path, error = generate_image(
                scene["image_prompt"],
                number,
            )

            if error:
                save_project()
                return None, error

            st.session_state.images[
                str(number)
            ] = image_path

            save_project()

        completed += 1

        progress.progress(
            min(
                1.0,
                completed / total_tasks,
            )
        )

        for clip_no in range(
            1,
            clips_per_scene + 1,
        ):
            key = (
                f"{number}_{clip_no}"
            )

            video_path = (
                st.session_state.videos.get(
                    key
                )
            )

            if existing_file(
                video_path
            ):
                status.write(
                    f"⏭️ Scene {number} "
                    f"clip {clip_no}: "
                    "پہلے سے تیار ہے۔"
                )

                all_clips.append(
                    video_path
                )

                completed += 1

                progress.progress(
                    min(
                        1.0,
                        completed / total_tasks,
                    )
                )

                continue

            status.write(
                f"🎥 Scene {number}: "
                f"AI motion {clip_no}..."
            )

            video_path, error = create_ai_video(
                image_path,
                scene["motion_prompt"],
                number,
                clip_no,
            )

            if error:
                save_project()
                return None, error

            st.session_state.videos[
                key
            ] = video_path

            all_clips.append(
                video_path
            )

            save_project()

            completed += 1

            progress.progress(
                min(
                    1.0,
                    completed / total_tasks,
                )
            )

    status.write(
        "✂️ Clips کو جوڑا جا رہا ہے..."
    )

    silent_movie = os.path.join(
        PROJECT_DIR,
        "full_movie_silent.mp4",
    )

    silent_movie, error = combine_clips(
        all_clips,
        silent_movie,
        duration_minutes * 60,
    )

    if error:
        save_project()
        return None, error

    completed += 1

    progress.progress(
        min(
            1.0,
            completed / total_tasks,
        )
    )

    status.write(
        "🎵 Full movie music بن رہی ہے..."
    )

    final_movie, error = add_full_music(
        silent_movie,
        music_style,
        music_track,
        music_volume,
    )

    if error:
        save_project()
        return None, error

    st.session_state.full_movie = (
        final_movie
    )

    save_project()

    progress.progress(1.0)

    status.write(
        "✅ Final movie تیار ہے۔"
    )

    return final_movie, None


# =========================================================
