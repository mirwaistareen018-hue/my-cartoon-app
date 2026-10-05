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

st.set_page_config(
    page_title="AI Cartoon Movie Studio",
    page_icon="🎬",
    layout="wide",
)


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
    text = str(scene.get("text", "") or "")
    chars = scene.get("characters", [])
    if not isinstance(chars, list):
        chars = []
    chars = [str(x) for x in chars if str(x).strip()]
    return {
        "number": int(scene.get("number", number) or number),
        "text": text,
        "action": str(
            scene.get("action", "")
            or "natural character movement and cinematic environmental motion"
        ),
        "characters": chars,
        "prompt": str(scene.get("prompt", "") or text),
    }


def load_state():
    if not STATE.exists():
        return fresh_state()
    try:
        with open(STATE, "r", encoding="utf-8") as file:
            data = json.load(file)
        result = fresh_state()
        if isinstance(data, dict):
            result.update(data)
        scenes = result.get("scenes", [])
        result["scenes"] = [
            normalize_scene(scene, i)
            for i, scene in enumerate(scenes, 1)
        ]
        for key in ("images", "videos"):
            if not isinstance(result.get(key), dict):
                result[key] = {}
        return result
    except Exception:
        return fresh_state()


def save_state(data):
    APP.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    tmp.replace(STATE)


state = load_state()


def clean(text):
    return re.sub(r"\s+", " ", str(text).strip())


def split_story(text):
    text = clean(text)
    if not text:
        return []

    parts = [
        p.strip()
        for p in re.split(r"(?<=[.!?۔؟])\s+", text)
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
                    " ".join(words[i:i + 24])
                    for i in range(0, len(words), 24)
                )
        return result

    words = text.split()
    size = 18
    return [
        " ".join(words[i:i + size])
        for i in range(0, len(words), size)
    ]


def find_characters(text):
    names = []
    common = [
        "crow", "fox", "lion", "rabbit", "cat", "dog", "bird",
        "mouse", "farmer", "boy", "girl", "king", "queen",
        "کوا", "لومڑی", "شیر", "خرگوش", "بلی", "کتا", "پرندہ",
        "کسان", "لڑکا", "لڑکی", "بادشاہ", "ملکہ",
    ]
    low = text.lower()
    for item in common:
        if item.lower() in low and item not in names:
            names.append(item)
    return names


def detect_action(text):
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
        (["sleep", "sleeps", "سو"], "rests with gentle natural movement"),
    ]
    for words, result in rules:
        if any(word in low for word in words):
            return result
    return "natural character movement, expressive reaction, and cinematic environmental motion"


def make_scenes(story):
    chars = find_characters(story)
    scenes = []

    for number, text in enumerate(split_story(story), 1):
        act = detect_action(text)
        char_text = ", ".join(chars) if chars else "main cartoon characters"
        prompt = (
            "High quality 3D family-friendly cartoon movie frame. "
            "Characters: " + char_text + ". "
            "Story moment: " + text + ". "
            "Action: " + act + ". "
            "Consistent character appearance, cinematic composition, "
            "colorful lighting, detailed environment."
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


def get_token():
    return st.secrets.get(
        "HF_TOKEN",
        os.environ.get("HF_TOKEN", ""),
    )


def generate_image(scene):
    if InferenceClient is None:
        return None, "huggingface_hub is not installed."

    token = get_token()
    if not token:
        return None, "HF_TOKEN is missing from Streamlit Secrets."

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
        output = IMAGES / f"scene_{scene.get('number', 1)}.png"
        image.save(output)
        return str(output), None
    except Exception as exc:
        return None, str(exc)


def generate_motion(image_path, scene, clip_number):
    try:
        from gradio_client import Client, handle_file
    except Exception:
        return None, "gradio_client is not installed."

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as temp:
            temp_path = temp.name

        shutil.copyfile(image_path, temp_path)

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
            + ", smooth natural movement, natural body movement, "
            + "natural environmental movement, cinematic camera movement, "
            + "stable character appearance"
        )

        negative = (
            "static image, frozen frame, blurry, distorted, "
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
            return None, "AI video service returned no file."

        number = int(scene.get("number", 1) or 1)
        output = VIDEOS / (
            f"scene_{number}_clip_{clip_number}.mp4"
        )

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


def make_music(seconds, style):
    seconds = max(5, int(seconds))
    rate = 22050
    count = seconds * rate
    time_axis = np.arange(count, dtype=np.float32) / rate

    frequencies = {
        "Happy / Cheerful": 261.63,
        "Cute / Sweet": 329.63,
        "Farm / Nature": 220.00,
        "Magical / Fantasy": 392.00,
        "Funny Cartoon": 294.00,
        "Peaceful": 196.00,
        "Cinematic": 146.83,
    }

    freq = frequencies.get(style, 196.0)

    signal = (
        np.sin(2 * np.pi * freq * time_axis)
        + 0.45 * np.sin(2 * np.pi * freq * 1.5 * time_axis)
        + 0.20 * np.sin(2 * np.pi * freq * 2 * time_axis)
    )

    fade = min(2.0, seconds / 2)
    fade_count = max(1, int(fade * rate))
    envelope = np.ones(count, dtype=np.float32)

    envelope[:fade_count] = np.linspace(0, 1, fade_count)
    envelope[-fade_count:] = np.linspace(1, 0, fade_count)

    audio = np.clip(
        signal * envelope * 0.12,
        -1,
        1,
    )

    output = MUSIC / "background_music.wav"
    pcm = (audio * 32767).astype(np.int16)

    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())

    return str(output)


def moviepy_modules():
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
        return VideoFileClip, concatenate_videoclips
    except Exception:
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            return VideoFileClip, concatenate_videoclips
        except Exception:
            return None, None


def video_paths():
    result = []
    videos = state.get("videos", {})
    if not isinstance(videos, dict):
        return result

    for key in sorted(videos):
        path = videos.get(key)
        if path and Path(path).exists():
            result.append(path)

    return result


def video_duration(paths):
    VideoFileClip, _ = moviepy_modules()

    if VideoFileClip is None:
        return 0.0

    total = 0.0

    for path in paths:
        clip = None
        try:
            clip = VideoFileClip(path)
            total += float(clip.duration or 0)
        except Exception:
            pass
        finally:
            if clip:
                try:
                    clip.close()
                except Exception:
                    pass

    return total


def join_videos(paths):
    VideoFileClip, concatenate = moviepy_modules()

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

        final = concatenate(
            clips,
            method="compose",
        )

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


st.title("🎬 AI Cartoon Movie Studio")
st.caption(
    "A-to-Z: Story → Smart Scenes → AI Images → AI Motion → Music → Final MP4"
)

with st.sidebar:
    st.header("Project Status")
    st.write("Scenes:", len(state.get("scenes", [])))
    st.write("Images:", len(state.get("images", {})))
    st.write("Videos:", len(state.get("videos", {})))
    st.write(
        "Final Movie:",
        "Ready" if state.get("final_movie") else "Not ready",
    )

story_tab, ai_tab, movie_tab = st.tabs(
    ["1. Story & Scenes", "2. AI Production", "3. Final Movie"]
)


with story_tab:
    st.subheader("📝 Full Story")

    story = st.text_area(
        "Story / کہانی",
        value=str(state.get("story", "") or ""),
        height=280,
        placeholder="Write your complete story here...",
    )

    if st.button(
        "🧠 Create Smart Scene Plan",
        type="primary",
    ):
        if not story.strip():
            st.warning("پہلے کہانی لکھیں۔")
        else:
            state["story"] = story.strip()
            state["scenes"] = make_scenes(story)
            state["images"] = {}
            state["videos"] = {}
            state["music"] = None
            state["final_movie"] = None
            save_state(state)
            st.success(
                f"{len(state['scenes'])} scenes تیار ہو گئے۔"
            )

    scenes = state.get("scenes", [])

    for index, raw_scene in enumerate(scenes, 1):
        scene = normalize_scene(raw_scene, index)

        with st.expander(
            f"Scene {scene.get('number', index)}"
        ):
            st.write(
                scene.get("text", "")
                or "Scene text not available."
            )
            st.write(
                "**Action:**",
                scene.get("action")
                or "Natural cinematic movement",
            )

            chars = scene.get("characters", [])
            if not isinstance(chars, list):
                chars = []

            st.write(
                "**Characters:**",
                ", ".join(
                    str(item)
                    for item in chars
                    if str(item).strip()
                )
                or "Main characters",
            )


with ai_tab:
    st.subheader("🤖 AI Production")

    clips_per_scene = st.number_input(
        "Motion clips per scene",
        min_value=1,
        max_value=3,
        value=1,
        step=1,
    )

    music_style = st.selectbox(
        "🎵 Background Music",
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

    if st.button(
        "🖼️ Generate All Images",
        type="primary",
    ):
        if not scenes:
            st.warning("پہلے Scene Plan بنائیں۔")
        else:
            bar = st.progress(0.0)
            total = len(scenes)

            for index, raw_scene in enumerate(scenes, 1):
                scene = normalize_scene(raw_scene, index)
                key = str(scene.get("number", index))

                old = state.get("images", {}).get(key)

                if old and Path(old).exists():
                    st.write(
                        f"Scene {index}/{total}: already complete."
                    )
                else:
                    st.write(
                        f"Scene {index}/{total}: generating..."
                    )

                    path, error = generate_image(scene)

                    if error:
                        st.error(
                            f"Scene {scene.get('number', index)}: {error}"
                        )
                        break

                    state.setdefault("images", {})[key] = path
                    save_state(state)

                bar.progress(index / total)

            st.success("Image generation step finished.")


    if st.button("🎬 Generate All AI Motion"):
        if not state.get("images"):
            st.warning("پہلے images generate کریں۔")
        else:
            total = max(
                1,
                len(scenes) * int(clips_per_scene),
            )
            completed = 0
            bar = st.progress(0.0)

            for index, raw_scene in enumerate(scenes, 1):
                scene = normalize_scene(raw_scene, index)
                key = str(scene.get("number", index))
                image_path = state.get("images", {}).get(key)

                if not image_path or not Path(image_path).exists():
                    st.error(
                        f"Scene {key}: image missing."
                    )
                    continue

                for clip_number in range(
                    1,
                    int(clips_per_scene) + 1,
                ):
                    video_key = f"{key}_{clip_number}"
                    old = state.get("videos", {}).get(video_key)

                    if old and Path(old).exists():
                        completed += 1
                        bar.progress(completed / total)
                        continue

                    st.write(
                        f"Scene {key}, clip {clip_number}: generating..."
                    )

                    path, error = generate_motion(
                        image_path,
                        scene,
                        clip_number,
                    )

                    if error:
                        st.error(
                            f"Scene {key}, clip {clip_number}: {error}"
                        )
                        st.warning(
                            "Generation یہاں رک گئی ہے۔ "
                            "پہلے سے بنا ہوا کام محفوظ ہے؛ "
                            "دوبارہ چلانے سے resume ہوگا۔"
                        )
                        save_state(state)
                        break

                    state.setdefault(
                        "videos",
                        {},
                    )[video_key] = path

                    save_state(state)

                    completed += 1
                    bar.progress(completed / total)


    if st.button("🎵 Generate Background Music"):
        paths = video_paths()

        if not paths:
            st.warning(
                "پہلے motion clips بنائیں۔"
            )
        else:
            VideoFileClip, _ = moviepy_modules()

            if VideoFileClip is None:
                st.error(
                    "MoviePy is not available."
                )
            else:
                clips = []
                total_seconds = 0.0

                try:
                    for path in paths:
                        clip = VideoFileClip(path)
                        clips.append(clip)
                        total_seconds += float(
                            clip.duration or 0
                        )

                    state["music"] = make_music(
                        total_seconds,
                        music_style,
                    )

                    save_state(state)
                    st.success(
                        "Background music تیار ہے۔"
                    )

                except Exception as exc:
                    st.error(str(exc))

                finally:
                    for clip in clips:
                        try:
                            clip.close()
                        except Exception:
                            pass


with movie_tab:
    st.subheader("🎞️ Final Movie")

    paths = video_paths()

    st.write(
        "Available motion clips:",
        len(paths),
    )

    if paths:
        st.write(
            "Estimated duration:",
            f"{video_duration(paths):.1f} seconds",
        )

    if st.button(
        "🎞️ Build Final MP4",
        type="primary",
    ):
        if not paths:
            st.warning(
                "ابھی video clips موجود نہیں۔"
            )
        else:
            with st.spinner(
                "Final movie تیار ہو رہی ہے..."
            ):
        
