import os
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
# PROJECT DIRECTORIES
# ============================================================

APP_DIR = Path("cartoon_project")
IMAGE_DIR = APP_DIR / "images"
VIDEO_DIR = APP_DIR / "videos"
MUSIC_DIR = APP_DIR / "music"
STATE_FILE = APP_DIR / "state.json"

for folder in (IMAGE_DIR, VIDEO_DIR, MUSIC_DIR):
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# STREAMLIT PAGE
# ============================================================

st.set_page_config(
    page_title="AI Cartoon Movie Studio",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 AI Cartoon Movie Studio")
st.caption("Story → Scenes → Images → Motion → Music → Movie")


# ============================================================
# STATE
# ============================================================

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
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        state = default_state()
        state.update(data)

        return state

    except Exception:
        return default_state()


def save_state(state):
    APP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = STATE_FILE.with_suffix(".tmp")

    with open(
        temp_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2,
        )

    temp_file.replace(STATE_FILE)


# ============================================================
# STORY → SCENES
# ============================================================

def split_story(text):
    text = " ".join(
        text.strip().split()
    )

    if not text:
        return []

    parts = []
    current = ""

    for word in text.split():
        current = (
            current + " " + word
        ).strip()

        if len(current.split()) >= 35:
            parts.append(current)
            current = ""

    if current:
        parts.append(current)

    return parts


def detect_action(text):
    low = text.lower()

    if any(
        x in low
        for x in [
            "fly",
            "flies",
            "flying",
            "اڑ",
        ]
    ):
        return (
            "The character flies naturally "
            "through the scene."
        )

    if any(
        x in low
        for x in [
            "walk",
            "walking",
            "چل",
        ]
    ):
        return (
            "The character walks naturally "
            "through the scene."
        )

    if any(
        x in low
        for x in [
            "run",
            "running",
            "دوڑ",
        ]
    ):
        return (
            "The character runs naturally "
            "through the scene."
        )

    if any(
        x in low
        for x in [
            "drink",
            "drinks",
            "پیتا",
        ]
    ):
        return (
            "The character moves to the water "
            "and drinks naturally."
        )

    if any(
        x in low
        for x in [
            "look",
            "looks",
            "دیکھ",
        ]
    ):
        return (
            "The character looks around "
            "and reacts naturally."
        )

    return (
        "Natural character movement and "
        "cinematic environmental motion."
    )


def make_scenes(story):
    chunks = split_story(story)

    return [
        {
            "number": i,
            "text": text,
            "action": detect_action(text),
        }
        for i, text in enumerate(
            chunks,
            1,
        )
    ]


# ============================================================
# HUGGING FACE TOKEN
# ============================================================

def hf_token():
    try:
        return st.secrets.get(
            "HF_TOKEN",
            os.environ.get(
                "HF_TOKEN",
                "",
            ),
        )
    except Exception:
        return os.environ.get(
            "HF_TOKEN",
            "",
        )


# ============================================================
# IMAGE GENERATION
# ============================================================

def generate_image(
    prompt,
    number,
):
    if InferenceClient is None:
        return (
            None,
            "huggingface_hub is not installed.",
        )

    token = hf_token()

    if not token:
        return (
            None,
            "HF_TOKEN is missing from Streamlit Secrets.",
        )

    try:
        client = InferenceClient(
            provider="auto",
            token=token,
        )

        full_prompt = (
            "High quality 3D cartoon movie frame, "
            "family friendly, cinematic lighting, "
            "colorful environment, consistent character, "
            "high quality animation style. "
            + prompt
        )

        image = client.text_to_image(
            full_prompt,
            model=(
                "black-forest-labs/"
                "FLUX.1-schnell"
            ),
        )

        output = (
            IMAGE_DIR
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
# AI VIDEO GENERATION
# ============================================================

def create_ai_video(
    image_path,
    motion_prompt,
    number,
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
            "gradio_client is not installed.",
        )

    if not image_path:
        return (
            None,
            "Image path is empty.",
        )

    if not Path(image_path).exists():
        return (
            None,
            f"Input image was not found: {image_path}",
        )

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
            "zerogpu-aoti/"
            "wan2-2-fp8da-aoti-faster",
            max_workers=1,
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
            "static image, frozen image, "
            "blurry, distorted, deformed character, "
            "extra limbs, flickering, unstable face, "
            "warped body, bad anatomy"
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

        if isinstance(
            result,
            (list, tuple),
        ):
            generated = result[0]
        else:
            generated = result

        if not generated:
            return (
                None,
                "AI video service returned no video.",
            )

        if isinstance(
            generated,
            dict,
        ):
            generated = (
                generated.get("path")
                or generated.get("url")
                or generated.get("name")
            )

        output = (
            VIDEO_DIR
            / (
                f"scene_{number}"
                f"_clip_{clip_number}.mp4"
            )
        )

        if isinstance(
            generated,
            str,
        ):
            source = Path(generated)

            if source.exists():
                shutil.copyfile(
                    source,
                    output,
                )

                return (
                    str(output),
                    None,
                )

            return (
                None,
                (
                    "Generated video file "
                    f"was not found: {generated}"
                ),
            )

        return (
            None,
            "AI video response format "
            "was not recognized.",
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
            except Exception:
                pass


# ============================================================
# BACKGROUND MUSIC
# ============================================================

def create_music(
    duration_seconds,
    style,
):
    duration = max(
        5,
        int(duration_seconds),
    )

    sample_rate = 22050

    total_samples = (
        duration * sample_rate
    )

    t = (
        np.arange(
            total_samples,
            dtype=np.float32,
        )
        / sample_rate
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

    frequency = frequencies.get(
        style,
        196.0,
    )

    signal = (
        np.sin(
            2
            * np.pi
            * frequency
            * t
        )
        + 0.5
        * np.sin(
            2
            * np.pi
            * frequency
            * 1.5
            * t
        )
        + 0.25
        * np.sin(
            2
            * np.pi
            * frequency
            * 2
            * t
        )
    )

    fade_seconds = min(
        2.0,
        duration / 2,
    )

    envelope = np.ones(
        total_samples,
        dtype=np.float32,
    )

    fade_samples = int(
        fade_seconds
        * sample_rate
    )

    if fade_samples > 0:
        envelope[
            :fade_samples
        ] = np.linspace(
            0,
            1,
            fade_samples,
        )

        envelope[
            -fade_samples:
        ] = np.linspace(
            1,
            0,
            fade_samples,
        )

    audio = np.clip(
        signal
        * envelope
        * 0.12,
        -1,
        1,
    )

    output = (
        MUSIC_DIR
        / "background_music.wav"
    )

    pcm = (
        audio * 32767
    ).astype(
        np.int16
    )

    # IMPORTANT:
    # All parentheses are properly closed here.
    with wave.open(
        str(output),
        "wb",
    ) as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(
            sample_rate
        )
        wav.writeframes(
            pcm.tobytes()
        )

    return str(output)


# ============================================================
# MOVIEPY IMPORTS
# ============================================================

def moviepy_imports():
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
# FINAL MOVIE
# ============================================================

def combine_videos(
    paths,
    music_style,
):
    (
        VideoFileClip,
        AudioFileClip,
        concatenate_videoclips,
    ) = moviepy_imports()

    if VideoFileClip is None:
        return (
            None,
            "MoviePy is not available.",
        )

    clips = []
    final_clip = None
    music_clip = None

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
            APP_DIR
            / "final_cartoon_movie.mp4"
        )

        final_clip = concatenate_videoclips(
            clips,
            method="compose",
        )

        # Create background music
        music_path = create_music(
            final_clip.duration,
            music_style,
        )

        if (
            music_path
            and Path(music_path).exists()
        ):
            music_clip = AudioFileClip(
                music_path
            )

            if (
                music_clip.duration
                > final_clip.duration
            ):
                try:
                    music_clip = (
                        music_clip.subclipped(
                            0,
                            final_clip.duration,
                        )
                    )
                except AttributeError:
                    music_clip = (
                        music_clip.subclip(
                            0,
                            final_clip.duration,
                        )
                    )

            else:
                try:
                    music_clip = (
                        music_clip.with_duration(
                            final_clip.duration
                        )
                    )
                except AttributeError:
                    music_clip = (
                        music_clip.set_duration(
                            final_clip.duration
                        )
                    )

            try:
                final_clip = (
                    final_clip.with_audio(
                        music_clip
                    )
                )
            except AttributeError:
                final_clip = (
                    final_clip.set_audio(
                        music_clip
                    )
                )

        final_clip.write_videofile(
            str(output),
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        return (
            str(output),
            None,
        )

    except Exception as exc:
        return (
            None,
            str(exc),
        )

    finally:
        if music_clip is not None:
            try:
                music_clip.close()
            except Exception:
                pass

        if final_clip is not None:
            try:
                final_clip.close()
            except Exception:
                pass

        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass


# ============================================================
# LOAD STATE
# ============================================================

state = load_state()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header(
        "Project Status"
    )

    st.write(
        "Scenes:",
        len(
            state["scenes"]
        ),
    )

    st.write(
        "Images:",
        len(
            state["images"]
        ),
    )

    st.write(
        "Videos:",
        len(
            state["videos"]
        ),
    )

    st.write(
        "Final movie:",
        (
            "Ready"
            if state["final_movie"]
            else "Not ready"
        ),
    )


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "1. Story",
        "2. Generate",
        "3. Final Movie",
    ]
)


# ============================================================
# TAB 1 — STORY
# ============================================================

with tab1:

    st.subheader(
        "اپنی مکمل کہانی یہاں لکھیں"
    )

    story = st.text_area(
        "Story / کہانی",
        value=state["story"],
        height=240,
        placeholder=(
            "Example: A thirsty crow "
            "flies over a forest..."
        ),
    )

    if st.button(
        "Create Scene Plan",
        type="primary",
    ):

        if not story.strip():

            st.warning(
                "پہلے کہانی لکھیں۔"
            )

        else:

            state["story"] = (
                story.strip()
            )

            state["scenes"] = (
                make_scenes(story)
            )

            # New story means old
            # generated assets are invalid.
            state["images"] = {}
            state["videos"] = {}
            state["music"] = None
            state["final_movie"] = None

            save_state(state)

            st.success(
                f"{len(state['scenes'])} "
                "scenes تیار ہو گئے۔"
            )

    for scene in state["scenes"]:

        st.write(
            f"**Scene {scene['number']}** "
            f"— {scene['text']}"
        )

        st.caption(
            "Action: "
            + scene["action"]
        )


# ============================================================
# TAB 2 — GENERATE
# ============================================================

with tab2:

    st.subheader(
        "AI Generation"
    )

    clip_count = st.number_input(
        "Motion clips per scene",
        min_value=1,
        max_value=3,
        value=1,
        step=1,
    )

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


    # --------------------------------------------------------
    # GENERATE IMAGES
    # --------------------------------------------------------

    if st.button(
        "Generate Images",
        type="primary",
    ):

        if not state["scenes"]:

            st.warning(
                "پہلے Scene Plan بنائیں۔"
            )

        else:

            progress = st.progress(
                0.0
            )

            image_failed = False

            for i, scene in enumerate(
                state["scenes"],
                1,
            ):

                key = str(
                    scene["number"]
                )

                old_image = state[
                    "images"
                ].get(key)

                if (
                    old_image
                    and Path(
                        old_image
                    ).e
