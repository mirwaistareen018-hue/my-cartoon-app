import os
import re
import json
import math
import shutil
import tempfile
import wave
from pathlib import Path

import numpy as np
import streamlit as st

try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None

APP_DIR = Path("cartoon_project")
IMAGE_DIR = APP_DIR / "images"
VIDEO_DIR = APP_DIR / "videos"
MUSIC_DIR = APP_DIR / "music"
STATE_FILE = APP_DIR / "state.json"

for folder in (IMAGE_DIR, VIDEO_DIR, MUSIC_DIR):
    folder.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="AI Cartoon Movie Studio",
    page_icon="🎬",
    layout="wide"
)


def default_state():
    return {
        "scenes": [],
        "images": {},
        "videos": {},
        "movie": None,
        "music": None,
    }


def load_state():
    if not STATE_FILE.exists():
        return default_state()

    try:
        data = json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )

        state = default_state()

        if isinstance(data, dict):
            state.update(data)

        return state

    except Exception:
        return default_state()


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8",
    )


def split_story(story):
    text = re.sub(
        r"\s+",
        " ",
        story.strip()
    )

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?۔])\s+",
        text
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if len(parts) <= 12:
        return parts

    size = math.ceil(
        len(parts) / 12
    )

    return [
        " ".join(
            parts[i:i + size]
        )
        for i in range(
            0,
            len(parts),
            size
        )
    ][:12]


def detect_action(text):
    lower = text.lower()

    if any(
        word in lower
        for word in (
            "fly",
            "flies",
            "اڑ",
            "پرواز"
        )
    ):
        return (
            "The character flies naturally "
            "through the environment."
        )

    if any(
        word in lower
        for word in (
            "walk",
            "walking",
            "run",
            "runs",
            "چل",
            "دوڑ"
        )
    ):
        return (
            "The character walks or runs "
            "naturally."
        )

    if any(
        word in lower
        for word in (
            "drink",
            "drinks",
            "پیت",
            "پانی"
        )
    ):
        return (
            "The character drinks naturally "
            "and reacts to the water."
        )

    if any(
        word in lower
        for word in (
            "look",
            "looks",
            "see",
            "sees",
            "دیکھ",
            "نظر"
        )
    ):
        return (
            "The character looks around "
            "and reacts naturally."
        )

    if any(
        word in lower
        for word in (
            "happy",
            "laugh",
            "laughs",
            "خوش",
            "ہنستا"
        )
    ):
        return (
            "The character reacts happily "
            "with natural body movement."
        )

    if any(
        word in lower
        for word in (
            "pick",
            "picks",
            "drop",
            "drops",
            "stone",
            "stones",
            "اٹھ",
            "پتھر"
        )
    ):
        return (
            "The character picks up and "
            "drops an object naturally."
        )

    return (
        "The characters perform the main "
        "action with natural movement."
    )


def make_scenes(story):
    scenes = []

    for number, text in enumerate(
        split_story(story),
        1
    ):
        scenes.append(
            {
                "number": number,
                "story": text,
                "action": detect_action(text),
                "prompt": (
                    "A high quality colorful 3D "
                    "cartoon movie scene, "
                    "cinematic composition, "
                    "consistent character design, "
                    "expressive faces, detailed "
                    "environment. "
                    + text
                ),
            }
        )

    return scenes


def generate_image(
    prompt,
    number
):
    token = os.getenv(
        "HF_TOKEN"
    )

    if not token:
        return (
            None,
            "HF_TOKEN is missing from Streamlit Secrets."
        )

    if InferenceClient is None:
        return (
            None,
            "huggingface_hub is not installed."
        )

    try:
        client = InferenceClient(
            token=token
        )

        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell",
            provider="auto",
        )

        path = (
            IMAGE_DIR
            / f"scene_{number}.png"
        )

        image.save(path)

        return (
            str(path),
            None
        )

    except Exception as exc:
        return (
            None,
            str(exc)
        )


def create_ai_video(
    image_path,
    motion_prompt,
    number,
    clip_number
):
    try:
        from gradio_client import (
            Client,
            handle_file
        )
    except Exception:
        return (
            None,
            "gradio_client is not installed."
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as tmp:
            temp_path = tmp.name

        shutil.copyfile(
            image_path,
            temp_path
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

        negative = (
            "static image, frozen frame, "
            + "blurry, distorted, "
            + "deformed character, "
            + "extra limbs, flickering, "
            + "unstable face, warped body, "
            + "bad anatomy"
        )

        result = client.predict(
            handle_file(temp_path),
            prompt,
            6,
            negative,
            3.5,
            1,
            1,
            42,
            True,
            api_name="/generate_video",
        )

        generated = (
            result[0]
            if isinstance(
                result,
                (list, tuple)
            )
            else result
        )

        if not generated:
            return (
                None,
                "The AI video service returned no video file."
            )

        output = (
            VIDEO_DIR
            / f"scene_{number}_clip_{clip_number}.mp4"
        )

        if isinstance(
            generated,
            str
        ):
            shutil.copyfile(
                generated,
                output
            )

            return (
                str(output),
                None
            )

        return (
            None,
            "The AI video response format was not recognized."
        )

    except Exception as exc:
        return (
            None,
            str(exc)
        )

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def create_music(
    minutes,
    style,
    track
):
    duration = max(
        10,
        int(minutes * 60)
    )

    rate = 22050
    total = duration * rate

    styles = {
        "Happy / Cheerful": [
            261.63,
            329.63,
            392.00,
            523.25
        ],
        "Cute / Sweet": [
            329.63,
            392.00,
            493.88,
            659.25
        ],
        "Farm / Nature": [
            220.00,
            277.18,
            329.63,
            440.00
        ],
        "Magical / Fantasy": [
            261.63,
            311.13,
            369.99,
            466.16
        ],
        "Funny Cartoon": [
            293.66,
            349.23,
            440.00,
            587.33
        ],
        "Peaceful": [
            196.00,
            246.94,
            293.66,
            392.00
        ],
        "Cinematic": [
            130.81,
            164.81,
            196.00,
            261.63
        ],
    }

    notes = styles.get(
        style,
        styles["Happy / Cheerful"]
    )

    note_len = max(
        1,
        int(rate * 0.6)
    )

    wave_data = np.zeros(
        total,
        dtype=np.float32
    )

    for start in range(
        0,
        total,
        note_len
    ):
        index = (
            start // note_len + track
        ) % len(notes)

        count = min(
            note_len,
            total - start
        )

        tt = (
            np.arange(
                count,
                dtype=np.float32
            )
            / rate
        )

        tone = (
            0.16
            * np.sin(
                2
                * np.pi
                * notes[index]
                * tt
            )
        )

        fade_len = min(
            300,
            count
        )

        if fade_len > 1:
            fade = np.linspace(
                0,
                1,
                fade_len,
                dtype=np.float32
            )

            tone[:fade_len] *= fade
            tone[-fade_len:] *= fade[::-1]

        wave_data[
            start:start + count
        ] += tone

    pcm = np.clip(
        wave_data,
        -0.8,
        0.8
    )

    pcm = (
        pcm * 32767
    ).astype(
        np.int16
    )

    safe_style = (
        style
        .split("/")[0]
        .strip()
        .replace(
            " ",
            "_"
        )
    )

    path = (
        MUSIC_DIR
        / f"music_{safe_style}_{track}.wav"
    )

    with wave.open(
        str(path),
        "wb"
    ) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(
            pcm.tobytes()
        )

    return str(path)


def import_moviepy():
    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
            concatenate_videoclips
        )

        return (
            VideoFileClip,
            AudioFileClip,
            concatenate_videoclips,
            None
        )

    except Exception:
        try:
            from moviepy.editor import (
                VideoFileClip,
                AudioFileClip,
                concatenate_videoclips
            )

            return (
                VideoFileClip,
                AudioFileClip,
                concatenate_videoclips,
                None
            )

        except Exception as exc:
            return (
                None,
                None,
                None,
                str(exc)
            )


def combine_videos(
    paths,
    output
):
    (
        VideoFileClip,
        _,
        concatenate_videoclips,
        error
    ) = import_moviepy()

    if error:
        return (
            None,
            error
        )

    clips = []
    final = None

    try:
        for path in paths:
            clips.append(
                VideoFileClip(path)
            )

        if not clips:
            return (
                None,
                "No video clips were found."
            )

        final = concatenate_videoclips(
            clips,
            method="compose"
        )

        final.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        return (
            output,
            None
        )

    except Exception as exc:
        return (
            None,
            str(exc)
        )

    finally:
        if final:
            try:
                final.close()
            except Exception:
                pass

        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass


def add_music(
    video_path,
    music_path,
    output,
    volume
):
    (
        VideoFileClip,
        AudioFileClip,
        _,
        error
    ) = import_moviepy()

    if error:
        return (
            None,
            error
        )

    video = None
    audio = None
    final = None

    try:
        video = VideoFileClip(
            video_path
        )

        audio = AudioFileClip(
            music_path
        )

        if audio.duration > video.duration:
            audio = audio.subclip(
                0,
                video.duration
            )

        elif (
            audio.duration < video.duration
            and hasattr(
                audio,
                "audio_loop"
            )
        ):
            audio = audio.audio_loop(
                duration=video.duration
            )

        if hasattr(
            audio,
            "volumex"
        ):
            audio = audio.volumex(
                volume
            )

        elif hasattr(
            audio,
            "with_volume_scaled"
        ):
            audio = audio.with_volume_scaled(
                volume
            )

        if hasattr(
            video,
            "set_audio"
        ):
            final = video.set_audio(
                audio
            )

        else:
            final = video.with_audio(
                audio
            )

        final.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        return (
            output,
            None
        )

    except Exception as exc:
        return (
            None,
            str(exc)
        )

    finally:
        for obj in (
            final,
            audio,
            video
        ):
            if obj:
                try:
                    obj.close()
                except Exception:
                    pass


state = load_state()


st.title(
    "🎬 AI Cartoon Movie Studio"
)

st.caption(
    "Urdu + English | Story → Scenes → AI Images → AI Motion → Music → Movie"
)


with st.sidebar:
    st.header(
        "Project Status"
    )

    st.write(
        "App: OK"
    )

    st.write(
        "Story: "
        + (
            "OK"
            if state["scenes"]
            else "Waiting"
        )
    )

    st.write(
        "Images: "
        + str(
            len(
                state["images"]
            )
        )
    )

    st.write(
        "Motion: "
        + str(
            len(
                state["videos"]
            )
        )
    )

    st.write(
        "Resume System: Enabled"
    )

    st.write(
        "Music: "
        + (
            "OK"
            if state["music"]
            else "Waiting"
        )
    )


story = st.text_area(
    "📝 مکمل کہانی یہاں paste کریں / Paste your full story",
    height=220,
    placeholder="Example: A thirsty crow was flying through a forest and found a pot of water.",
)


col1, col2, col3 = st.columns(
    3
)


with col1:
    duration = st.selectbox(
        "Movie target duration",
        [2, 3, 4, 5],
        index=0
    )


with col2:
    clips_per_scene = st.selectbox(
        "Clips per scene",
        [1, 2, 3],
        index=0
    )


with col3:
    music_style = st.selectbox(
        "Background Music",
        [
            "Happy / Cheerful",
            "Cute / Sweet",
            "Farm / Nature",
            "Magical / Fantasy",
            "Funny Cartoon",
            "Peaceful",
            "Cinematic",
        ],
    )


track = st.selectbox(
    "Music variation",
    [1, 2, 3, 4, 5]
)


volume = st.slider(
    "Music volume",
    0.05,
    0.50,
    0.16,
    0.01
)


a, b, c = st.columns(
    3
)


with a:
    make_plan = st.button(
        "1️⃣ Make Scene Plan",
        use_container_width=True
    )


with b:
    make_images = st.button(
        "2️⃣ Generate Images",
        use_container_width=True
    )


with c:
    make_motion = st.button(
        "3️⃣ Generate AI Motion",
        use_container_width=True
    )


if make_plan:
    if not story.strip():
        st.warning(
            "پہلے کہانی لکھیں۔"
        )

    else:
        state["scenes"] = make_scenes(
            story
        )

        state["images"] = {}
        state["videos"] = {}
        state["movie"] = None
        state["music"] = None

        save_state(
            state
        )

        st.success(
            "Scene plan تیار ہو گیا۔"
        )


if state["scenes"]:
    st.subheader(
        "🎞️ Scene Plan"
    )

    for scene in state["scenes"]:
        st.markdown(
            f"**Scene {scene['number']}** — {scene['story']}  \n"
            f"**Action:** {scene['action']}"
        )


if make_images:
    if not state["scenes"]:
        st.warning(
            "پہلے Scene Plan بنائیں۔"
        )

    else:
        progress = st.progress(
            0
        )

        total = len(
            state["scenes"]
        )

        for index, scene in enumerate(
            state["scenes"],
            1
        ):
            key = str(
                scene["number"]
            )

            existing = state[
                "images"
            ].get(key)

            if (
                not existing
                or not Path(
                    existing
                ).exists()
            ):
                path, error = generate_image(
                    scene["prompt"],
                    scene["number"]
                )

                if error:
                    st.error(
                        f"Scene {key}: {error}"
                    )
                    break

                state[
                    "images"
                ][key] = path

                save_state(
                    state
                )

            progress.progress(
                index / total
            )

        st.success(
            "Images process مکمل ہو گیا۔"
        )


if make_motion:
    if not state["images"]:
        st.warning(
            "پہلے images بنائیں۔"
        )

    else:
        total = (
            len(
                state["scenes"]
            )
            * clips_per_scene
        )

        done = 0

        progress = st.progress(
            0
        )

        stopped = False

        for scene in state["scenes"]:
            if stopped:
                break

            key = str(
                scene["number"]
            )

            image_path = state[
                "images"
            ].get(key)

            if not image_path:
                continue

            for clip_no in range(
                1,
                clips_per_scene + 1
            ):
                vkey = (
                    f"{key}_{clip_no}"
                )

                existing = state[
                    "videos"
                ].get(vkey)

                if (
                    existing
                    and Path(
                        existing
                    ).exists()
                ):
                    done += 1

                    progress.progress(
                        min(
                            done / total,
                            1.0
                        )
                    )

                    continue

                path, error = create_ai_video(
                    image_path,
                    scene["action"],
                    scene["number"],
          
