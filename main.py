import os
import re
import json
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


# ============================================================
# APP DIRECTORIES
# ============================================================

APP = Path("cartoon_project")
IMAGES = APP / "images"
VIDEOS = APP / "videos"
MUSIC = APP / "music"
STATE = APP / "state.json"

for folder in (APP, IMAGES, VIDEOS, MUSIC):
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Cartoon Movie Studio",
    page_icon="🎬",
    layout="wide",
)


# ============================================================
# STATE
# ============================================================

def fresh_state():
    return {
        "story": "",
        "scenes": [],
        "images": {},
        "videos": {},
        "music": None,
        "final_movie": None,
    }


def normalize_scene(scene, number):
    if not isinstance(scene, dict):
        scene = {}

    try:
        scene_number = int(
            scene.get("number", number) or number
        )
    except (TypeError, ValueError):
        scene_number = number

    text = str(
        scene.get("text", "") or ""
    )

    chars = scene.get(
        "characters",
        [],
    )

    if not isinstance(chars, list):
        chars = []

    chars = [
        str(x)
        for x in chars
        if str(x).strip()
    ]

    return {
        "number": scene_number,
        "text": text,
        "action": str(
            scene.get("action", "")
            or "natural character movement and cinematic environmental motion"
        ),
        "characters": chars,
        "prompt": str(
            scene.get("prompt", "")
            or text
        ),
    }


def load_state():
    if not STATE.exists():
        return fresh_state()

    try:
        with STATE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        result = fresh_state()

        if isinstance(data, dict):
            result.update(data)

        scenes = result.get(
            "scenes",
            [],
        )

        if not isinstance(
            scenes,
            list,
        ):
            scenes = []

        result["scenes"] = [
            normalize_scene(
                scene,
                i,
            )
            for i, scene in enumerate(
                scenes,
                1,
            )
        ]

        for key in (
            "images",
            "videos",
        ):
            if not isinstance(
                result.get(key),
                dict,
            ):
                result[key] = {}

        return result

    except Exception:
        return fresh_state()


def save_state(data):
    APP.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp = STATE.with_suffix(
        ".tmp"
    )

    with tmp.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    tmp.replace(STATE)


state = load_state()


# ============================================================
# STORY HELPERS
# ============================================================

def clean(text):
    return re.sub(
        r"\s+",
        " ",
        str(text).strip(),
    )


def split_story(text):
    text = clean(text)

    if not text:
        return []

    parts = [
        p.strip()
        for p in re.split(
            r"(?<=[.!?۔؟])\s+",
            text,
        )
        if p.strip()
    ]

    if len(parts) > 1:
        result = []

        for part in parts:
            words = part.split()

            if len(words) <= 24:
                result.append(part)
            else:
                result.extend(
                    " ".join(
                        words[i:i + 24]
                    )
                    for i in range(
                        0,
                        len(words),
                        24,
                    )
                )

        return result

    words = text.split()
    size = 18

    return [
        " ".join(
            words[i:i + size]
        )
        for i in range(
            0,
            len(words),
            size,
        )
    ]


def find_characters(text):
    names = []

    common = [
        "crow",
        "fox",
        "lion",
        "rabbit",
        "cat",
        "dog",
        "bird",
        "mouse",
        "farmer",
        "boy",
        "girl",
        "king",
        "queen",
        "کوا",
        "لومڑی",
        "شیر",
        "خرگوش",
        "بلی",
        "کتا",
        "پرندہ",
        "کسان",
        "لڑکا",
        "لڑکی",
        "بادشاہ",
        "ملکہ",
    ]

    low = text.lower()

    for item in common:
        if item.lower() in low:
            if item not in names:
                names.append(item)

    return names


def detect_action(text):
    low = text.lower()

    rules = [
        (
            [
                "fly",
                "flies",
                "flying",
                "اڑ",
            ],
            "flies naturally through the environment",
        ),
        (
            [
                "walk",
                "walking",
                "چل",
            ],
            "walks naturally with body movement",
        ),
        (
            [
                "run",
                "running",
                "دوڑ",
            ],
            "runs naturally through the scene",
        ),
        (
            [
                "drink",
                "drinks",
                "پانی پیتا",
                "پیتا",
            ],
            "moves to water and drinks naturally",
        ),
        (
            [
                "look",
                "looks",
                "دیکھ",
            ],
            "looks around and reacts naturally",
        ),
        (
            [
                "pick",
                "picks",
                "اٹھا",
            ],
            "reaches forward and picks up the object",
        ),
        (
            [
                "drop",
                "drops",
                "ڈال",
            ],
            "moves the object and drops it naturally",
        ),
        (
            [
                "happy",
                "smile",
                "خوش",
                "مسکرات",
            ],
            "becomes happy and reacts cheerfully",
        ),
        (
            [
                "sleep",
                "sleeps",
                "سو",
            ],
            "rests with gentle natural movement",
        ),
    ]

    for words, result in rules:
        if any(
            word in low
            for word in words
        ):
            return result

    return (
        "natural character movement, "
        "expressive reaction, and "
        "cinematic environmental motion"
    )


def make_scenes(story):
    chars = find_characters(
        story
    )

    scenes = []

    for number, text in enumerate(
        split_story(story),
        1,
    ):
        act = detect_action(
            text
        )

        char_text = (
            ", ".join(chars)
            if chars
            else "main cartoon characters"
        )

        prompt = (
            "High quality 3D family-friendly "
            "cartoon movie frame. "
            "Characters: "
            + char_text
            + ". "
            "Story moment: "
            + text
            + ". "
            "Action: "
            + act
            + ". "
            "Consistent character appearance, "
            "cinematic composition, "
            "colorful lighting, "
            "detailed environment."
        )

        scenes.append(
            normalize_scene(
                {
                    "number": number,
                    "text": text,
                    "action": act,
                    "characters": list(chars),
                    "prompt": prompt,
                },
                number,
            )
        )

    return scenes


# ============================================================
# HUGGING FACE
# ============================================================

def get_token():
    try:
        token = st.secrets.get(
            "HF_TOKEN",
            "",
        )
    except Exception:
        token = ""

    return (
        token
        or os.environ.get(
            "HF_TOKEN",
            "",
        )
    )


def generate_image(scene):
    if InferenceClient is None:
        return (
            None,
            "huggingface_hub is not installed. "
            "Install it with: "
            "pip install huggingface_hub",
        )

    token = get_token()

    if not token:
        return (
            None,
            "HF_TOKEN is missing from "
            "Streamlit Secrets or environment variables.",
        )

    try:
        client = InferenceClient(
            provider="auto",
            api_key=token,
        )

        prompt = str(
            scene.get("prompt")
            or scene.get("text")
            or "A family friendly cartoon scene"
        )

        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell",
        )

        number = int(
            scene.get(
                "number",
                1,
            )
            or 1
        )

        output = (
            IMAGES
            / f"scene_{number}.png"
        )

        image.save(output)

        return (
            str(output),
            None,
        )

    except Exception as exc:
        return (
            None,
            str(exc),
        )


# ============================================================
# AI MOTION
# ============================================================

def generate_motion(
    image_path,
    scene,
    clip_number,
):
    try:
        from gradio_client import (
            Client,
            handle_file,
        )
    except Exception:
        return (
            None,
            "gradio_client is not installed. "
            "Install it with: "
            "pip install gradio_client",
        )

    temp_path = None

    try:
        if not image_path:
            return (
                None,
                "Image path is empty.",
            )

        if not Path(
            image_path
        ).exists():
            return (
                None,
                f"Image file not found: {image_path}",
            )

        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as temp:
            temp_path = temp.name

        shutil.copyfile(
            image_path,
            temp_path,
        )

        client = Client(
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster",
            max_workers=1,
        )

        action = str(
            scene.get("action")
            or "natural character movement and cinematic motion"
        )

        prompt = (
            action
            + ", smooth natural movement, "
            + "natural body movement, "
            + "natural environmental movement, "
            + "cinematic camera movement, "
            + "stable character appearance"
        )

        negative = (
            "static image, frozen frame, blurry, "
            "distorted, deformed character, "
            "extra limbs, flickering, "
            "unstable face, warped body, "
            "bad anatomy"
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
                (list, tuple),
            )
            else result
        )

        if not generated:
            return (
                None,
                "AI video service returned no file.",
            )

        number = int(
            scene.get(
                "number",
                1,
            )
            or 1
        )

        output = (
            VIDEOS
            / f"scene_{number}_clip_{clip_number}.mp4"
        )

        if isinstance(
            generated,
            str,
        ):
            generated_path = Path(
                generated
            )

            if not generated_path.exists():
                return (
                    None,
                    "Generated video file was not found.",
                )

            shutil.copyfile(
                generated_path,
                output,
            )

            return (
                str(output),
                None,
            )

        if isinstance(
            generated,
            dict,
        ):
            possible_path = (
                generated.get("path")
                or generated.get("video")
            )

            if (
                possible_path
                and Path(
                    str(possible_path)
                ).exists()
            ):
                shutil.copyfile(
                    str(possible_path),
                    output,
                )

                return (
                    str(output),
                    None,
                )

        return (
            None,
            "AI video response format was not recognized.",
        )

    except Exception as exc:
        return (
            None,
            str(exc),
        )

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ============================================================
# MUSIC
# ============================================================

def make_music(
    seconds,
    style,
):
    seconds = max(
        5,
        int(seconds),
    )

    rate = 22050
    count = seconds * rate

    time_axis = (
        np.arange(
            count,
            dtype=np.float32,
        )
        / rate
    )

    frequencies = {
        "Happy / Cheerful": 261.63,
        "Cute / Sweet": 329.63,
        "Farm / Nature": 220.00,
        "Magical / Fantasy": 392.00,
        "Funny Cartoon": 294.00,
        "Peaceful": 196.00,
        "Cinematic": 146.83,
    }

    freq = frequencies.get(
        style,
        196.0,
    )

    signal = (
        np.sin(
            2
            * np.pi
            * freq
            * time_axis
        )
        + 0.45
        * np.sin(
            2
            * np.pi
            * freq
            * 1.5
            * time_axis
        )
        + 0.20
        * np.sin(
            2
            * np.pi
            * freq
            * 2
            * time_axis
        )
    )

    fade_count = max(
        1,
        int(
            min(
                2.0,
                seconds / 2,
            )
            * rate
        ),
    )

    envelope = np.ones(
        count,
        dtype=np.float32,
    )

    envelope[
        :fade_count
    ] = np.linspace(
        0,
        1,
        fade_count,
    )

    envelope[
        -fade_count:
    ] = np.linspace(
        1,
        0,
        fade_count,
    )

    audio = np.clip(
        signal
        * envelope
        * 0.12,
        -1,
        1,
    )

    output = (
        MUSIC
        / "background_music.wav"
    )

    pcm = (
        audio * 32767
    ).astype(np.int16)

    with wave.open(
        str(output),
        "wb",
    ) as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(
            pcm.tobytes()
        )

    return str(output)


# ============================================================
# MOVIEPY
# ============================================================

def moviepy_modules():
    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
            concatenate_videoclips,
        )

        return (
            VideoFileClip,
            AudioFileClip,
            concatenate_videoclips,
        )

    except Exception:
        try:
            from moviepy.editor import (
                VideoFileClip,
                AudioFileClip,
                concatenate_videoclips,
            )

            return (
                VideoFileClip,
                AudioFileClip,
                concatenate_videoclips,
            )

        except Exception:
            return (
                None,
                None,
                None,
            )


# ============================================================
# VIDEO HELPERS
# ============================================================

def video_paths():
    result = []

    videos = state.get(
        "videos",
        {},
    )

    if not isinstance(
        videos,
        dict,
    ):
        return result

    def sort_key(key):
        parts = re.findall(
            r"\d+",
            str(key),
        )

        if parts:
            return tuple(
                int(x)
                for x in parts
            )

        return (
            999999,
        )

    for key in sorted(
        videos,
        key=sort_key,
    ):
        path = videos.get(key)

        if (
            path
            and Path(path).exists()
        ):
            result.append(path)

    return result


def video_duration(paths):
    (
        VideoFileClip,
        _,
        _,
    ) = moviepy_modules()

    if VideoFileClip is None:
        return 0.0

    total = 0.0

    for path in paths:
        clip = None

        try:
            clip = VideoFileClip(
                path
            )

            total += float(
                clip.duration
                or 0
            )

        except Exception:
            pass

        finally:
            if clip:
                try:
                    clip.close()
                except Exception:
                    pass

    return total


def join_videos(
    paths,
    music_path=None,
):
    (
        VideoFileClip,
        AudioFileClip,
        concatenate,
    ) = moviepy_modules()

    if (
        VideoFileClip is None
        or concatenate is None
    ):
        return (
            None,
            "MoviePy is not available. "
            "Install it with: pip install moviepy",
        )

    clips = []
    final = None
    music = None

    try:
        for path in paths:
            if (
                path
                and Path(path).exists()
            ):
                clips.append(
                    VideoFileClip(path)
                )

        if not clips:
            return (
                None,
                "No video clips are available.",
            )

        output = (
            APP
            / "final_cartoon_movie.mp4"
        )

        final = concatenate(
            clips,
            method="compose",
        )

        if (
            music_path
            and AudioFileClip is not None
            and Path(music_path).exists()
        ):
            try:
                music = AudioFileClip(
                    music_path
                )

                if (
                    music.duration
                    and final.duration
                    and music.duration
                    > final.duration
                ):
                    try:
                        music = music.subclipped(
                            0,
                            final.duration,
                        )
                    except AttributeError:
        
