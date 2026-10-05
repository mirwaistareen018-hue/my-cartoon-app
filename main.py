import os
import re
import io
import json
import math
import time
import wave
import shutil
import random
import asyncio
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image
from huggingface_hub import InferenceClient


# =========================================================
# CONFIG
# =========================================================

APP_DIR = Path("cartoon_project")
IMAGE_DIR = APP_DIR / "images"
VIDEO_DIR = APP_DIR / "videos"
AUDIO_DIR = APP_DIR / "audio"
MUSIC_DIR = APP_DIR / "music"
SFX_DIR = APP_DIR / "sfx"

PROJECT_FILE = APP_DIR / "project.json"

for folder in [
    APP_DIR,
    IMAGE_DIR,
    VIDEO_DIR,
    AUDIO_DIR,
    MUSIC_DIR,
    SFX_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)


IMAGE_MODEL = os.getenv(
    "IMAGE_MODEL",
    "black-forest-labs/FLUX.1-schnell"
)

VIDEO_MODEL = os.getenv(
    "VIDEO_MODEL",
    ""
)

VIDEO_SPACE = os.getenv(
    "VIDEO_SPACE",
    ""
)

VIDEO_API = os.getenv(
    "VIDEO_API",
    "/generate_video"
)

TEXT_MODEL = os.getenv(
    "TEXT_MODEL",
    "meta-llama/Llama-3.1-8B-Instruct"
)


# =========================================================
# SECRETS
# =========================================================

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


def hf_token():
    return get_secret("HF_TOKEN")


# =========================================================
# PROJECT STATE
# =========================================================

def default_project():
    return {
        "title": "",
        "language": "Urdu",
        "visual_style": (
            "original preschool 3D cartoon, colorful rounded characters, "
            "soft cinematic lighting, expressive faces, playful environment"
        ),
        "story": "",
        "characters": [],
        "locations": [],
        "scenes": [],
        "images": [],
        "videos": [],
        "voices": [],
        "music": [],
        "sfx": [],
        "final_movie": "",
    }


def load_project():
    if PROJECT_FILE.exists():
        try:
            return json.loads(
                PROJECT_FILE.read_text(encoding="utf-8")
            )
        except Exception:
            pass

    return default_project()


def save_project(project):
    PROJECT_FILE.write_text(
        json.dumps(
            project,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json(text):
    text = text.strip()

    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.I
    )

    text = re.sub(
        r"```\s*",
        "",
        text
    )

    first = text.find("{")
    last = text.rfind("}")

    if first == -1 or last == -1:
        raise ValueError("AI نے valid JSON واپس نہیں کیا۔")

    return json.loads(text[first:last + 1])


# =========================================================
# AI STORY PLANNER
# =========================================================

def create_story_plan(story, language, style):
    token = hf_token()

    if not token:
        raise RuntimeError(
            "HF_TOKEN Streamlit Secrets میں add کریں۔"
        )

    client = InferenceClient(
        api_key=token,
        provider="auto"
    )

    system_prompt = """
You are a professional children's animated movie production planner.

Turn the user's script into a complete production JSON.

The movie must use an ORIGINAL preschool 3D cartoon look.
Do not copy any existing TV show, movie, character or copyrighted style.

Return ONLY valid JSON.

Required structure:

{
  "title": "...",
  "logline": "...",
  "visual_style": "...",

  "characters": [
    {
      "id": "char_1",
      "name": "...",
      "role": "...",
      "species": "...",
      "age_description": "...",
      "appearance": "...",
      "clothing": "...",
      "colors": "...",
      "personality": "...",
      "voice_description": "...",
      "character_prompt": "..."
    }
  ],

  "locations": [
    {
      "id": "loc_1",
      "name": "...",
      "description": "...",
      "environment": "...",
      "colors": "...",
      "lighting": "...",
      "location_prompt": "..."
    }
  ],

  "scenes": [
    {
      "id": "scene_1",
      "title": "...",
      "duration_seconds": 5,
      "location_id": "loc_1",
      "character_ids": ["char_1"],
      "story_summary": "...",
      "action": "...",
      "dialogue": [
        {
          "character_id": "char_1",
          "text": "..."
        }
      ],
      "camera": "...",
      "lighting": "...",
      "image_prompt": "...",
      "animation_prompt": "...",
      "negative_prompt": "...",
      "sound_effects": ["..."],
      "music_mood": "..."
    }
  ]
}

IMPORTANT:

1. Keep characters visually consistent.
2. Every scene must reference existing character IDs.
3. Every scene must reference an existing location.
4. Make image prompts extremely descriptive.
5. Make animation prompts describe motion only.
6. Avoid changing character clothes/colors between scenes.
7. Keep the story suitable for children.
8. Dialogue should be short enough for animation.
9. Make scenes 4-8 seconds each.
10. Return valid JSON only.
"""

    user_prompt = f"""
Language: {language}

Visual style:
{style}

Story:
{story}
"""

    result = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        max_tokens=9000,
        temperature=0.35
    )

    raw = result.choices[0].message.content

    return extract_json(raw)


# =========================================================
# CHARACTER CONSISTENCY
# =========================================================

def character_prompt(project, character_ids):
    chars = []

    lookup = {
        c["id"]: c
        for c in project.get("characters", [])
    }

    for cid in character_ids:
        c = lookup.get(cid)

        if not c:
            continue

        chars.append(
            f"""
Character:
Name: {c.get('name', '')}
Species: {c.get('species', '')}
Age: {c.get('age_description', '')}
Appearance: {c.get('appearance', '')}
Clothing: {c.get('clothing', '')}
Colors: {c.get('colors', '')}
Personality: {c.get('personality', '')}
"""
        )

    return "\n".join(chars)


def build_scene_image_prompt(project, scene):
    base_style = project.get(
        "visual_style",
        "original preschool 3D cartoon"
    )

    chars = character_prompt(
        project,
        scene.get("character_ids", [])
    )

    location = ""

    for loc in project.get("locations", []):
        if loc.get("id") == scene.get("location_id"):
            location = f"""
Location:
{loc.get('name', '')}
{loc.get('description', '')}
Environment:
{loc.get('environment', '')}
Colors:
{loc.get('colors', '')}
Lighting:
{loc.get('lighting', '')}
"""
            break

    return f"""
{base_style}

CHARACTER CONSISTENCY:
{chars}

{location}

SCENE:
{scene.get('story_summary', '')}

ACTION:
{scene.get('action', '')}

CAMERA:
{scene.get('camera', '')}

LIGHTING:
{scene.get('lighting', '')}

IMAGE DESCRIPTION:
{scene.get('image_prompt', '')}

High quality 3D children's animation frame,
consistent character design,
same clothing,
same colors,
same proportions,
expressive faces,
clean composition,
cinematic depth,
soft lighting,
detailed environment,
16:9 landscape,
no text,
no logo,
no watermark.
"""


# =========================================================
# IMAGE GENERATION
# =========================================================

def generate_image(prompt, filename):
    token = hf_token()

    if not token:
        raise RuntimeError("HF_TOKEN missing.")

    client = InferenceClient(
        api_key=token,
        provider="auto"
    )

    image = client.text_to_image(
        prompt=prompt,
        model=IMAGE_MODEL,
        width=1280,
        height=720,
        num_inference_steps=4
    )

    path = IMAGE_DIR / filename

    image.save(path)

    return str(path)


# =========================================================
# VIDEO GENERATION - HUGGING FACE INFERENCE
# =========================================================

def generate_video_hf(
    image_path,
    prompt,
    filename,
    negative_prompt=""
):
    token = hf_token()

    if not token:
        raise RuntimeError("HF_TOKEN missing.")

    if not VIDEO_MODEL:
        raise RuntimeError(
            "VIDEO_MODEL set نہیں ہے۔"
        )

    client = InferenceClient(
        api_key=token,
        provider="auto"
    )

    video_bytes = client.image_to_video(
        image=image_path,
        prompt=prompt,
        negative_prompt=negative_prompt,
        model=VIDEO_MODEL,
        num_inference_steps=20,
        guidance_scale=5.0
    )

    output = VIDEO_DIR / filename

    output.write_bytes(video_bytes)

    return str(output)


# =========================================================
# VIDEO GENERATION - GRADIO SPACE
# =========================================================

def generate_video_space(
    image_path,
    prompt,
    filename,
    negative_prompt=""
):
    if not VIDEO_SPACE:
        raise RuntimeError(
            "VIDEO_SPACE set نہیں ہے۔"
        )

    from gradio_client import Client, handle_file

    token = hf_token()

    client = Client(
        VIDEO_SPACE,
        token=token if token else None
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # API arguments depend on the Space.
    #
    # Use client.view_api() to inspect them.
    # -----------------------------------------------------

    result = client.predict(
        handle_file(str(image_path)),
        prompt,
        6,
        negative_prompt,
        3.5,
        1,
        1,
        42,
        True,
        api_name=VIDEO_API
    )

    video_result = result

    if isinstance(result, (list, tuple)):
        video_result = result[0]

    if isinstance(video_result, dict):
        video_result = (
            video_result.get("video")
            or video_result.get("path")
            or video_result.get("url")
        )

    if not video_result:
        raise RuntimeError(
            "Video Space نے video result نہیں دیا۔"
        )

    output = VIDEO_DIR / filename

    if str(video_result).startswith("http"):
        import requests

        r = requests.get(
            str(video_result),
            timeout=300
        )

        r.raise_for_status()

        output.write_bytes(r.content)

    else:
        shutil.copyfile(
            str(video_result),
            str(output)
        )

    return str(output)


# =========================================================
# VIDEO BACKEND SELECTOR
# =========================================================

def generate_video(
    image_path,
    prompt,
    filename,
    negative_prompt=""
):

    # First preference:
    # Hugging Face Inference image-to-video
    if VIDEO_MODEL:
        return generate_video_hf(
            image_path,
            prompt,
            filename,
            negative_prompt
        )

    # Second preference:
    # Hugging Face Gradio Space
    if VIDEO_SPACE:
        return generate_video_space(
            image_path,
            prompt,
            filename,
            negative_prompt
        )

    raise RuntimeError(
        """
Video backend configured نہیں ہے.

Option A:
VIDEO_MODEL set کریں.

یا

Option B:
VIDEO_SPACE اور VIDEO_API set کریں.
"""
    )


# =========================================================
# TEXT TO SPEECH
# =========================================================

async def edge_tts_save(text, voice, output):
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice
    )

    await communicate.save(output)


def generate_tts(text, voice, filename):
    output = AUDIO_DIR / filename

    asyncio.run(
        edge_tts_save(
            text,
            voice,
            str(output)
        )
    )

    return str(output)


def choose_voice(language, index=0):
    voices = {
        "Urdu": [
            "ur-PK-AsadNeural",
            "ur-PK-UzmaNeural"
        ],
        "Hindi": [
            "hi-IN-MadhurNeural",
            "hi-IN-SwaraNeural"
        ],
        "English": [
            "en-US-GuyNeural",
            "en-US-JennyNeural"
        ]
    }

    lang_voices = voices.get(
        language,
        voices["English"]
    )

    return lang_voices[
        index % len(lang_voices)
    ]


# =========================================================
# SCENE VOICE
# =========================================================

def generate_scene_voice(
    project,
    scene,
    scene_number
):

    dialogue = scene.get(
        "dialogue",
        []
    )

    if not dialogue:
        return None

    language = project.get(
        "language",
        "Urdu"
    )

    audio_parts = []

    for i, line in enumerate(dialogue):

        text = line.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        voice = choose_voice(
            language,
            i
        )

        path = generate_tts(
            text,
            voice,
            f"scene_{scene_number}_voice_{i}.mp3"
        )

        audio_parts.append(path)

    if not audio_parts:
        return None

    # combine using moviepy
    from moviepy import (
        AudioFileClip,
        concatenate_audioclips
    )

    clips = [
        AudioFileClip(x)
        for x in audio_parts
    ]

    combined = concatenate_audioclips(
        clips
    )

    output = AUDIO_DIR / (
        f"scene_{scene_number}_dialogue.mp3"
    )

    combined.write_audiofile(
        str(output),
        logger=None
    )

    for clip in clips:
        clip.close()

    combined.close()

    return str(output)


# =========================================================
# PROCEDURAL MUSIC
# =========================================================

def create_music(
    duration,
    filename,
    mood="happy"
):

    sample_rate = 44100

    duration = max(
        1,
        float(duration)
    )

    t = np.linspace(
        0,
        duration,
        int(sample_rate * duration),
        endpoint=False
    )

    mood_notes = {
        "happy": [261.63, 329.63, 392.00],
        "playful": [293.66, 349.23, 440.00],
        "calm": [261.63, 329.63, 392.00],
        "adventure": [220.00, 277.18, 329.63],
        "funny": [392.00, 493.88, 587.33]
    }

    notes = mood_notes.get(
        mood.lower(),
        mood_notes["happy"]
    )

    audio = np.zeros_like(t)

    note_length = 0.6

    for i, start in enumerate(
        np.arange(0, duration, note_length)
    ):

        freq = notes[i % len(notes)]

        mask = (
            (t >= start) &
            (t < start + note_length)
        )

        local_t = (
            t[mask] - start
        )

        envelope = np.exp(
            -local_t * 3
        )

        audio[mask] += (
            0.12 *
            np.sin(
                2 * np.pi *
                freq *
                local_t
            ) *
            envelope
        )

    audio = np.clip(
        audio,
        -1,
        1
    )

    pcm = (
        audio * 32767
    ).astype(np.int16)

    output = MUSIC_DIR / filename

    with wave.open(
        str(output),
        "wb"
    ) as wf:

        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(
            pcm.tobytes()
        )

    return str(output)


# =========================================================
# SIMPLE SOUND EFFECTS
# =========================================================

def create_sfx(
    kind,
    filename,
    duration=0.4
):

    sr = 44100

    t = np.linspace(
        0,
        duration,
        int(sr * duration),
        endpoint=False
    )

    if kind == "whoosh":

        freq = np.linspace(
            800,
            150,
            len(t)
        )

        audio = (
            np.sin(
                2 * np.pi *
                freq * t
            )
            * np.exp(-5 * t)
            * 0.3
        )

    elif kind == "pop":

        audio = (
            np.sin(
                2 * np.pi *
                400 * t
            )
            * np.exp(-15 * t)
            * 0.35
        )

    elif kind == "step":

        audio = (
            np.sin(
                2 * np.pi *
                120 * t
            )
            * np.exp(-12 * t)
            * 0.3
        )

    elif kind == "magic":

        audio = (
            np.sin(
                2 * np.pi *
                900 * t
            )
            + 0.5 *
            np.sin(
                2 * np.pi *
                1400 * t
            )
        )

        audio *= np.exp(-3 * t) * 0.15

    else:

        audio = np.random.normal(
            0,
            0.03,
            len(t)
        )

    pcm = (
        np.clip(
            audio,
            -1,
            1
        ) * 32767
    ).astype(np.int16)

    output = SFX_DIR / filename

    with wave.open(
        str(output),
        "wb"
    ) as wf:

        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(
            pcm.tobytes()
        )

    return str(output)


# =========================================================
# VIDEO + AUDIO EDITING
# =========================================================

def edit_movie(
    project,
    video_paths,
    scene_audio,
    music_path
):

    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        concatenate_videoclips,
        CompositeAudioClip
    )

    clips = []

    for path in video_paths:

        clip = VideoFileClip(
            str(path)
        )

        clips.append(clip)

    if not clips:
        raise RuntimeError(
            "کوئی video clip نہیں بنی۔"
        )

    final = concatenate_videoclips(
        clips,
        method="compose"
    )

    audio_layers = []

    # Dialogue
    current_time = 0

    for audio_path, clip in zip(
        scene_audio,
        clips
    ):

        if audio_path:

            voice = AudioFileClip(
                str(audio_path)
            )

            voice = voice.with_start(
                current_time
            )

            audio_layers.append(
                voice
            )

        current_time += clip.duration

    # Background music
    if music_path:

        music = AudioFileClip(
            str(music_path)
        )

        if music.duration > final.duration:

            music = music.subclipped(
                0,
                final.duration
            )

        else:

            loops = []

            remaining = final.duration

            while remaining > 0:

                part = music.subclipped(
                    0,
                    min(
                        music.duration,
                        remaining
                    )
                )

                loops.append(part)

                remaining -= part.duration

            from moviepy import (
                concatenate_audioclips
            )

            music = concatenate_audioclips(
                loops
            )

        music = music.with_volume_scaled(
            0.25
        )

        audio_layers.append(
            music
        )

    if audio_layers:

        final_audio = CompositeAudioClip(
            audio_layers
        )

        final = final.with_audio(
            final_a)
