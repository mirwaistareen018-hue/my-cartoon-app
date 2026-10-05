import os
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
    layout="wide",
)

st.title("🎬 AI Cartoon Movie Studio")
st.caption("Story → Scenes → Images → Motion → Music → Movie")


def default_state():
    return {
        "story": "",
        "scenes": [],
        "images": {},
        "videos": {},
        "music": None,
        "final_movie": None,
    }


def load_state():
    if not STATE_FILE.exists():
        return default_state()

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        state = default_state()
        state.update(data)
        return state

    except Exception:
        return default_state()


def save_state(state):
    APP_DIR.mkdir(parents=True, exist_ok=True)

    tmp = STATE_FILE.with_suffix(".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
        )

    tmp.replace(STATE_FILE)


def split_story(text):
    text = " ".join(text.strip().split())

    if not text:
        return []

    parts = []
    current = ""

    for word in text.split():
        current = (current + " " + word).strip()

        if len(current.split()) >= 35:
            parts.append(current)
            current = ""

    if current:
        parts.append(current)

    return parts


def detect_action(text):
    low = text.lower()

    if any(x in low for x in ["fly", "flies", "flying", "اڑ"]):
        return "The character flies naturally through the scene."

    if any(x in low for x in ["walk", "walking", "چل"]):
        return "The character walks naturally through the scene."

    if any(x in low for x in ["run", "running", "دوڑ"]):
        return "The character runs naturally through the scene."

    if any(x in low for x in ["drink", "drinks", "پیتا"]):
        return "The character moves to the water and drinks naturally."

    if any(x in low for x in ["look", "looks", "دیکھ"]):
        return "The character looks around and reacts naturally."

    return "Natural character movement and cinematic environmental motion."


def make_scenes(story):
    chunks = split_story(story)

    return [
        {
            "number": i,
            "text": text,
            "action": detect_action(text),
        }
        for i, text in enumerate(chunks, 1)
    ]


def hf_token():
    return st.secrets.get(
        "HF_TOKEN",
        os.environ.get("HF_TOKEN", ""),
    )


def generate_image(prompt, number):
    if InferenceClient is None:
        return None, "huggingface_hub is not installed."

    token = hf_token()

    if not token:
        return None, "HF_TOKEN is missing from Streamlit Secrets."

    try:
        client = InferenceClient(
            provider="auto",
            token=token,
        )

        image = client.text_to_image(
            "High quality 3D cartoon movie frame, family friendly, "
            "cinematic lighting, colorful environment, consistent character. "
            + prompt,
            model="black-forest-labs/FLUX.1-schnell",
        )

        output = IMAGE_DIR / f"scene_{number}.png"

        image.save(output)

        return str(output), None

    except Exception as exc:
        return None, str(exc)


def create_ai_video(
    image_path,
    motion_prompt,
    number,
    clip_number,
):
    try:
        from gradio_client import Client, handle_file
    except Exception:
        return None, "gradio_client is not installed."

    if not image_path or not Path(image_path).exists():
        return None, f"Input image was not found: {image_path}"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as tmp:
            temp_path = tmp.name

        shutil.copyfile(
            image_path,
            temp_path,
        )

        client = Client(
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster",
            max_workers=1,
        )

        prompt = (
            motion_prompt
            + ", smooth natural movement, natural body movement, "
            + "natural environmental movement, cinematic camera movement, "
            + "stable character appearance"
        )

        negative = (
            "static image, frozen image, blurry, distorted, "
            "deformed character, extra limbs, flickering, "
            "unstable face, warped body, bad anatomy"
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
            if isinstance(result, (list, tuple))
            else result
        )

        if not generated:
            return None, "AI video service returned no video."

        if isinstance(generated, dict):
            generated = (
                generated.get("path")
                or generated.get("url")
                or generated.get("name")
            )

        output = VIDEO_DIR / (
            f"scene_{number}_clip_{clip_number}.mp4"
        )

        if isinstance(generated, str):
            source = Path(generated)

            if source.exists():
                shutil.copyfile(
                    source,
                    output,
                )

                return str(output), None

            return None, (
                f"Generated video file was not found: {generated}"
            )

        return None, (
            "AI video response format was not recognized."
        )

    except Exception as exc:
        return None, str(exc)

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def create_music(duration_seconds, style):
    duration = max(
        5,
        int(duration_seconds),
    )

    rate = 22050
    total = duration * rate

    t = (
        np.arange(total, dtype=np.float32)
        / rate
    )

    frequencies = {
        "Happy / Cheerful": 261.63,
        "Cute / Sweet": 329.63,
        "Farm / Nature": 220.0,
        "Magical / Fantasy": 392.0,
        "Funny Cartoon": 294.0,
        "Peaceful": 196.0,
        "Cinematic": 146.83,
    }

    freq = frequencies.get(
        style,
        196.0,
    )

    signal = (
        np.sin(2 * np.pi * freq * t)
        + 0.5 * np.sin(
            2 * np.pi * freq * 1.5 * t
        )
        + 0.25 * np.sin(
            2 * np.pi * freq * 2 * t
        )
    )

    fade = min(
        2.0,
        duration / 2,
    )

    envelope = np.ones(
        total,
        dtype=np.float32,
    )

    n = int(fade * rate)

    if n > 0:
        envelope[:n] = np.linspace(
            0,
            1,
            n,
        )

        envelope[-n:] = np.linspace(
            1,
            0,
            n,
        )

    audio = np.clip(
        signal * envelope * 0.12,
        -1,
        1,
    )

    output = MUSIC_DIR / "background_music.wav"

    pcm = (
        audio * 32767
    ).astype(np.int16)

    with wave.open(
        str(output),
        "wb",
           
