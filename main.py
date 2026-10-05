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

APP = Path("cartoon_project")
IMAGES = APP / "images"
VIDEOS = APP / "videos"
MUSIC = APP / "music"
STATE = APP / "state.json"

for folder in (IMAGES, VIDEOS, MUSIC):
    folder.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="AI Cartoon Movie Studio", page_icon="🎬", layout="wide")


def fresh_state():
    return {"story": "", "scenes": [], "images": {}, "videos": {}, "final_movie": None}


def load_state():
    if not STATE.exists():
        return fresh_state()
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = fresh_state()
        result.update(data)
        return result
    except Exception:
        return fresh_state()


def save_state(data):
    tmp = STATE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(STATE)


def clean(text):
    return re.sub(r"\s+", " ", text.strip())


def split_story(text):
    text = clean(text)
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"(?<=[.!?۔؟])\s+", text) if p.strip()]
    if len(parts) > 1:
        return parts
    words = text.split()
    size = 18
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


def characters(text):
    names = []
    for word in [
        "crow", "fox", "lion", "rabbit", "cat", "dog", "bird", "mouse",
        "farmer", "boy", "girl", "king", "queen",
        "کوا", "لومڑی", "شیر", "خرگوش", "بلی", "کتا", "پرندہ",
        "کسان", "لڑکا", "لڑکی", "بادشاہ", "ملکہ"
    ]:
        if word.lower() in text.lower() and word not in names:
            names.append(word)
    return names


def action(text):
    low = text.lower()
    rules = [
        (["fly", "flies", "flying", "اڑ"], "flies naturally through the environment"),
        (["walk", "walking", "چل"], "walks naturally with body movement"),
        (["run", "running", "دوڑ"], "runs naturally through the scene"),
        (["drink", "drinks", "پانی پیتا", "پیتا"], "moves to water and drinks naturally"),
        (["look", "looks", "دیکھ"], "looks around and reacts naturally"),
        (["pick", "picks", "اٹھا"], "reaches forward and picks up the object"),
        (["drop", "drops", "ڈال"], "moves the object and drops it naturally"),
        (["happy", "smile", "خوش", "مسکرات"], "becomes happy and reacts cheerfully"),
    ]
    for words, result in rules:
        if any(x in low for x in words):
            return result
    return "natural character movement, expressive reaction, and cinematic environmental motion"


def make_scenes(story):
    chars = characters(story)
    scenes = []
    for number, text in enumerate(split_story(story), 1):
        act = action(text)
        char_text = ", ".join(chars) if chars else "main cartoon characters"
        prompt = (
            "High quality 3D family-friendly cartoon movie frame. "
            "Characters: " + char_text + ". Story moment: " + text +
            ". Action: " + act +
            ". Consistent character appearance, cinematic composition, colorful lighting."
        )
        scenes.append({
            "number": number,
            "text": text,
            "action": act,
            "characters": chars,
            "prompt": prompt,
        })
    return scenes


def token():
    return st.secrets.get("HF_TOKEN", os.environ.get("HF_TOKEN", ""))


def make_image(scene):
    if InferenceClient is None:
        return None, "huggingface_hub is not installed."
    if not token():
        return None, "HF_TOKEN is missing from Streamlit Secrets."
    try:
        client = InferenceClient(provider="auto", api_key=token())
        image = client.text_to_image(
            scene["prompt"],
            model="black-forest-labs/FLUX.1-schnell",
        )
        path = IMAGES / f"scene_{scene['number']}.png"
        image.save(path)
        return str(path), None
    except Exception as exc:
        return None, str(exc)


def make_motion(image_path, scene, clip_number):
    try:
        from gradio_client import Client, handle_file
    except Exception:
        return None, "gradio_client is not installed."

    temp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp = f.name
        shutil.copyfile(image_path, temp)

        client = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster", max_workers=1)
        prompt = (
            scene["action"] +
            ", smooth natural movement, natural body movement, "
            "natural environment, cinematic camera movement, stable character appearance"
        )
        negative = (
            "static image, frozen frame, blurry, distorted, deformed character, "
            "extra limbs, flickering, unstable face, warped body, bad anatomy"
        )

        result = client.predict(
            handle_file(temp),
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
            return None, "AI video service returned no file."

        output = VIDEOS / f"scene_{scene['number']}_clip_{clip_number}.mp4"
        if isinstance(generated, str):
            shutil.copyfile(generated, output)
            return str(output), None
        return None, "AI video response format was not recognized."
    except Exception as exc:
        return None, str(exc)
    finally:
        if temp:
            try:
                os.remove(temp)
            except Exception:
                pass


def make_music(seconds, style):
    seconds = max(5, int(seconds))
    rate = 22050
    count = seconds * rate
    t = np.arange(count, dtype=np.float32) / rate
    freq = {
        "Happy / Cheerful": 261.63,
        "Cute / Sweet": 329.63,
        "Farm / Nature": 220.0,
        "Magical / Fantasy": 392.0,
        "Funny Cartoon": 294.0,
        "Peaceful": 196.0,
        "Cinematic": 146.83,
    }.get(style, 196.0)
    signal = (
        np.sin(2 * np.pi * freq * t)
        + 0.45 * np.sin(2 * np.pi * freq * 1.5 * t)
        + 0.2 * np.sin(2 * np.pi * freq * 2 * t)
    )
    fade = min(2, seconds / 2)
    n = int(fade * rate)
    env = np.ones(count, dtype=np.float32)
    env[:n] = np.linspace(0, 1, n)
    env[-n:] = np.linspace(1, 0, n)
    pcm = (np.clip(signal * env * 0.12, -1, 1) * 32767).astype(np.int16)
    output = MUSIC / "background_music.wav"
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())
    return str(output)


def moviepy():
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
        return VideoFileClip, concatenate_videoclips
    except Exception:
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            return VideoFileClip, concatenate_videoclips
        except Exception:
            return None, None


def join_videos(paths):
    VideoFileClip, concatenate = moviepy()
    if VideoFileClip is None:
        return None, "MoviePy is not available."
    clips = []
    try:
        for path in paths:
            if path and Path(path).exists():
                clips.append(VideoFileClip(path))
        if not clips:
            return None, "No video clips are available."
        output = APP / "final_cartoon_movie.mp4"
        final = concatenate(clips, method="compose")
        final.write_videofile(str(output), codec="libx264", audio_codec="aac", logger=None)
        final.close()
        for clip in clips:
            clip.close()
        return str(output), None
    except Exception as exc:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        return None, str(exc)


state = load_state()

st.title("🎬 AI Cartoon Movie Studio")
st.caption("A-to-Z: Story → Smart Scenes → Images → Motion → Music → Final MP4")

with st.sidebar:
    st.header("Project Status")
    st.write("Scenes:", len(state["scenes"]))
    st.write("Images:", len(state["images"]))
    st.write("Videos:", len(state["videos"]))
    st.write("Final Movie:", "Ready" if state["final_movie"] else "Not ready")

story_tab, ai_tab, movie_tab = st.tabs(["1. Story", "2. AI Production", "3. Final Movie"])

with story_tab:
    story = st.text_area(
        "Story / کہانی",
        value=state["story"],
        height=260,
        placeholder="Write your complete story here...",
    )
    if st.button("🧠 Create Smart Scene Plan", type="primary"):
        if not story.strip():
            st.warning("پہلے کہانی لکھیں۔")
        else:
            state["story"] = story.strip()
            state["scenes"] = make_scenes(story)
            state["images"] = {}
            state["videos"] = {}
            state["final_movie"] = None
            save_state(state)
            st.success(f"{len(state['scenes'])} scenes تیار ہو گئے۔")

    for scene in state["scenes"]:
        with st.expander(f"Scene {scene['number']}"):
            st.write(scene["text"])
            st.write("**Action:**", scene["action"])
            st.write("**Characters:**", ", ".join(scene["characters"]) or "Main characters")

with ai_tab:
    clips_per_scene = st.number_input(
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

    if st.button("🖼️ Generate All Images", type="primary"):
        if not state["scenes"]:
            st.warning("پہلے Scene Plan بنائیں۔")
        else:
            bar = st.progress(0.0)
            total = len(state["scenes"])
            for i, scene in enumerate(state["scenes"], 1):
                key = str(scene["number"])
                old = state["images"].get(key)
                if old and Path(old).exists():
                    st.write(f"Scene {i}/{total}: already complete.")
                else:
                    st.write(f"Scene {i}/{total}: generating...")
                    path, error = make_image(scene)
                    if error:
                        st.error(error)
                        break
                    state["images"][key] = path
                    save_state(state)
                bar.progress(i / total)

    if st.button("🎬 Generate All AI Motion"):
        if not state["images"]:
            st.warning("پہلے images generate کریں۔")
        else:
            total = len(state["scenes"]) * int(clips_per_scene)
            done = 0
            bar = st.progress(0.0)
            for scene in state["scenes"]:
                key = str(scene["number"])
                image = state["images"].get(key)
                if not image or not Path(image).exists():
                    st.error(f"Scene {key}: image missing.")
                    continue
                for clip_no in range(1, int(clips_per_scene) + 1):
                    video_key = f"{key}_{clip_no}"
                    old = state["videos"].get(video_key)
                    if old and Path(old).exists():
                        done += 1
                        bar.progress(done / total)
                        continue
                    st.write(f"Scene {key}, clip {clip_no}: generating...")
                    path, error = make_motion(image, scene, clip_no)
                    if error:
                        st.error(error)
                        st.warning("یہاں رک گیا ہے۔ پہلے سے بنا کام محفوظ ہے؛ دوبارہ چلانے سے resume ہوگا۔")
                        save_state(state)
                        break
                    state["videos"][video_key] = path
                    save_state(state)
                    done += 1
                    bar.progress(done / total)

    if st.button("🎵 Generate Background Music"):
        if not state["videos"]:
            st.warning("پہلے motion clips بنائیں۔")
        else:
            paths = [
                state["videos"][key]
                for key in sorted(state["videos"])
                if state["videos"].get(key) and Path(state["videos"][key]).exists()
            ]
            VideoFileClip, _ = moviepy()
            if VideoFileClip is None:
                st.error("MoviePy is not available.")
            else:
                total_seconds = 0
                clips = []
                try:
                    for path in paths:
                        clip = VideoFileClip(path)
                        clips.append(clip)
                        total_seconds += float(clip.duration or 0)
                    state["music"] = make_music(total_seconds, music_style)
                    save_state(state)
                    st.success("Background music تیار ہے۔")
                finally:
                    for clip in clips:
                        try:
                            clip.close()
                        except Exception:
                            pass

with movie_tab:
    paths = [
        state["videos"][key]
        for key in sorted(state["videos"])
        if state["videos"].get(key) and Path(state["videos"][key]).exists()
    ]
    st.write("Available motion clips:", len(paths))

    if st.button("🎞️ Build Final MP4", type="primary"):
        if not paths:
            st.warning("ابھی video clips موجود نہیں۔")
        else:
            with st.spinner("Final movie تیار ہو رہی ہے..."):
                final_path, error = join_videos(paths)
            if error:
                st.error(error)
            else:
                state["final_movie"] = final_path
                save_state(state)
                st.success("Final movie تیار ہے۔")

    if state["final_movie"] and Path(state["final_movie"]).exists():
        st.video(state["final_movie"])
        with open(state["final_movie"], "rb") as movie:
            st.download_button(
                "⬇️ Download Final Movie",
                movie,
                file_name="final_cartoon_movie.mp4",
                mime="video/mp4",
            )

st.divider()
st.caption("Resume data is saved in cartoon_project/state.json.")
        
