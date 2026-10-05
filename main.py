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

st.set_page_config(page_title="AI Cartoon Movie Studio", page_icon="🎬", layout="wide")
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
        json.dump(state, f, ensure_ascii=False, indent=2)
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
        {"number": i, "text": text, "action": detect_action(text)}
        for i, text in enumerate(chunks, 1)
    ]


def hf_token():
    return st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN", ""))


def generate_image(prompt, number):
    if InferenceClient is None:
        return None, "huggingface_hub is not installed."
    token = hf_token()
    if not token:
        return None, "HF_TOKEN is missing from Streamlit Secrets."
    try:
        client = InferenceClient(provider="auto", api_key=token)
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


def create_ai_video(image_path, motion_prompt, number, clip_number):
    try:
        from gradio_client import Client, handle_file
    except Exception:
        return None, "gradio_client is not installed."

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_path = tmp.name
        shutil.copyfile(image_path, temp_path)

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

        generated = result[0] if isinstance(result, (list, tuple)) else result
        if not generated:
            return None, "AI video service returned no video."

        output = VIDEO_DIR / f"scene_{number}_clip_{clip_number}.mp4"
        if isinstance(generated, str):
            shutil.copyfile(generated, output)
            return str(output), None
        return None, "AI video response format was not recognized."
    except Exception as exc:
        return None, str(exc)
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def create_music(duration_seconds, style):
    duration = max(5, int(duration_seconds))
    rate = 22050
    total = duration * rate
    t = np.arange(total, dtype=np.float32) / rate
    frequencies = {
        "Happy / Cheerful": 261.63,
        "Cute / Sweet": 329.63,
        "Farm / Nature": 220.0,
        "Magical / Fantasy": 392.0,
        "Funny Cartoon": 294.0,
        "Peaceful": 196.0,
        "Cinematic": 146.83,
    }
    freq = frequencies.get(style, 196.0)
    signal = (
        np.sin(2 * np.pi * freq * t)
        + 0.5 * np.sin(2 * np.pi * freq * 1.5 * t)
        + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    )
    fade = min(2.0, duration / 2)
    envelope = np.ones(total, dtype=np.float32)
    n = int(fade * rate)
    envelope[:n] = np.linspace(0, 1, n)
    envelope[-n:] = np.linspace(1, 0, n)
    audio = np.clip(signal * envelope * 0.12, -1, 1)
    output = MUSIC_DIR / "background_music.wav"
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())
    return str(output)


def moviepy_imports():
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
        return VideoFileClip, concatenate_videoclips
    except Exception:
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            return VideoFileClip, concatenate_videoclips
        except Exception:
            return None, None


def combine_videos(paths):
    VideoFileClip, concatenate_videoclips = moviepy_imports()
    if VideoFileClip is None:
        return None, "MoviePy is not available."
    clips = []
    try:
        for path in paths:
            if path and Path(path).exists():
                clips.append(VideoFileClip(path))
        if not clips:
            return None, "No video clips are available."
        output = APP_DIR / "final_cartoon_movie.mp4"
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            str(output),
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        final.close()
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        return str(output), None
    except Exception as exc:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        return None, str(exc)


state = load_state()

with st.sidebar:
    st.header("Project Status")
    st.write("Scenes:", len(state["scenes"]))
    st.write("Images:", len(state["images"]))
    st.write("Videos:", len(state["videos"]))
    st.write("Final movie:", "Ready" if state["final_movie"] else "Not ready")

tab1, tab2, tab3 = st.tabs(["1. Story", "2. Generate", "3. Final Movie"])

with tab1:
    st.subheader("اپنی مکمل کہانی یہاں لکھیں")
    story = st.text_area(
        "Story / کہانی",
        value=state["story"],
        height=240,
        placeholder="Example: A thirsty crow flies over a forest...",
    )

    if st.button("Create Scene Plan", type="primary"):
        if not story.strip():
            st.warning("پہلے کہانی لکھیں۔")
        else:
            state["story"] = story.strip()
            state["scenes"] = make_scenes(story)
            save_state(state)
            st.success(f"{len(state['scenes'])} scenes تیار ہو گئے۔")

    for scene in state["scenes"]:
        st.write(f"**Scene {scene['number']}** — {scene['text']}")
        st.caption("Action: " + scene["action"])

with tab2:
    st.subheader("AI Generation")
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

    if st.button("Generate Images", type="primary"):
        if not state["scenes"]:
            st.warning("پہلے Scene Plan بنائیں۔")
        else:
            progress = st.progress(0.0)
            for i, scene in enumerate(state["scenes"], 1):
                key = str(scene["number"])
                old = state["images"].get(key)
                if old and Path(old).exists():
                    st.write(f"Scene {i}: image already exists.")
                else:
                    st.write(f"Scene {i}: generating image...")
                    image_path, error = generate_image(
                        scene["text"] + ". Action: " + scene["action"],
                        scene["number"],
                    )
                    if error:
                        st.error(f"Scene {scene['number']}: {error}")
                        break
                    state["images"][key] = image_path
                    save_state(state)
                progress.progress(i / len(state["scenes"]))
            st.success("Image generation step finished.")

    if st.button("Generate AI Motion"):
        if not state["images"]:
            st.warning("پہلے Images generate کریں۔")
        else:
            total = len(state["scenes"]) * int(clip_count)
            done = 0
            progress = st.progress(0.0)

            for scene in state["scenes"]:
                key = str(scene["number"])
                image_path = state["images"].get(key)
                if not image_path or not Path(image_path).exists():
                    st.error(f"Scene {key} image missing.")
                    continue

                for clip_no in range(1, int(clip_count) + 1):
                    video_key = f"{key}_{clip_no}"
                    old = state["videos"].get(video_key)
                    if old and Path(old).exists():
                        done += 1
                        progress.progress(done / total)
                        continue

                    st.write(f"Generating Scene {key}, clip {clip_no}...")
                    path, error = create_ai_video(
                        image_path,
                        scene["action"],
                        scene["number"],
                        clip_no,
                    )
                    if error:
                        st.error(f"Scene {key}, clip {clip_no}: {error}")
                        st.warning(
                            "یہاں generation رک گئی ہے۔ پہلے سے بنا ہوا کام محفوظ ہے؛ "
                            "بعد میں دوبارہ چلانے سے resume ہو سکتا ہے."
                        )
                        save_state(state)
                        break

                    state["videos"][video_key] = path
                    save_state(state)
                    done += 1
                    progress.progress(done / total)

            st.success("Motion generation step finished.")

with tab3:
    st.subheader("Final Movie")

    video_paths = [
        state["videos"][key]
        for key in sorted(state["videos"])
        if state["videos"].get(key)
        and Path(state["videos"][key]).exists()
    ]

    st.write("Available video clips:", len(video_paths))

    if st.button("Build Final Movie", type="primary"):
        if not video_paths:
            st.warning("ابھی کوئی video clips موجود نہیں۔")
        else:
            with st.spinner("Movie جوڑی جا رہی ہے..."):
                final_path, error = combine_videos(video_paths)

            if error:
                st.error(error)
            else:
                state["final_movie"] = final_path
                save_state(state)
                st.success("Final movie تیار ہے۔")

    if state["final_movie"] and Path(state["final_movie"]).exists():
        st.video(state["final_movie"])
        with open(state["final_movie"], "rb") as f:
            st.download_button(
                "Download Movie",
                f,
                file_name="final_cartoon_movie.mp4",
                mime="video/mp4",
            )

st.divider()
st.caption("Resume data is saved inside cartoon_project.")
        
