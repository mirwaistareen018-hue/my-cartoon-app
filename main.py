
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


def load_state():
    if not STATE_FILE.exists():
        return {
            "scenes": [],
            "images": {},
            "videos": {},
            "movie": None,
            "music": None
        }

    try:
        return json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        return {
            "scenes": [],
            "images": {},
            "videos": {},
            "movie": None,
            "music": None
        }


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def split_story(story):
    text = re.sub(r"\s+", " ", story.strip())

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?۔])\s+",
        text
    )

    parts = [
        p.strip()
        for p in parts
        if p.strip()
    ]

    if len(parts) <= 12:
        return parts

    groups = []

    size = math.ceil(
        len(parts) / 12
    )

    for i in range(
        0,
        len(parts),
        size
    ):
        groups.append(
            " ".join(
                parts[i:i + size]
            )
        )

    return groups[:12]


def action_for(text):
    t = text.lower()

    if any(
        x in t
        for x in [
            "fly",
            "flies",
            "اڑ",
            "اڑتا"
        ]
    ):
        return (
            "the character flies naturally "
            "through the environment"
        )

    if any(
        x in t
        for x in [
            "walk",
            "runs",
            "run",
            "چل",
            "دوڑ"
        ]
    ):
        return (
            "the character walks or runs "
            "naturally"
        )

    if any(
        x in t
        for x in [
            "drink",
            "drinks",
            "پیت",
            "پانی"
        ]
    ):
        return (
            "the character drinks naturally"
        )

    if any(
        x in t
        for x in [
            "look",
            "sees",
            "دیکھ",
            "نظر"
        ]
    ):
        return (
            "the character looks around "
            "and reacts naturally"
        )

    if any(
        x in t
        for x in [
            "happy",
            "laugh",
            "خوش",
            "ہنستا"
        ]
    ):
        return (
            "the character reacts happily "
            "with natural body movement"
        )

    if any(
        x in t
        for x in [
            "pick",
            "drop",
            "stone",
            "اٹھ",
            "پتھر"
        ]
    ):
        return (
            "the character picks up and "
            "drops an object naturally"
        )

    return (
        "the characters perform the main "
        "action of the scene with natural movement"
    )


def make_scenes(story):
    sentences = split_story(story)

    scenes = []

    for i, text in enumerate(
        sentences,
        1
    ):
        scenes.append(
            {
                "number": i,
                "story": text,
                "action": action_for(text),
                "prompt": (
                    "A high quality colorful 3D "
                    "cartoon movie scene, cinematic "
                    "composition, consistent character "
                    "design, expressive faces, detailed "
                    "environment. "
                    + text
                )
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
            "HF_TOKEN Streamlit Secret میں موجود نہیں۔"
        )

    if InferenceClient is None:
        return (
            None,
            "huggingface_hub installed نہیں ہے۔"
        )

    try:
        client = InferenceClient(
            token=token
        )

        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell",
            provider="auto"
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
    clip_number=1
):
    try:
        from gradio_client import (
            Client,
            handle_file
        )
    except Exception:
        return (
            None,
            "gradio_client installed نہیں ہے۔"
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
            + "blurry, distorted, deformed character, "
            + "extra limbs, flickering, unstable face, "
            + "warped body, bad anatomy"
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
            api_name="/generate_video"
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
                "AI video file واپس نہیں آئی۔"
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
            "AI video response کا format سمجھ نہیں آیا۔"
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

    t = (
        np.arange(total, dtype=np.float32)
        / rate
    )

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
        ]
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

    for i in range(
        0,
        total,
        note_len
    ):
        idx = (
            i // note_len + track
        ) % len(notes)

        n = min(
            note_len,
            total - i
        )

        tt = (
            np.arange(
                n,
                dtype=np.float32
            )
            / rate
        )

        tone = (
            0.16
            * np.sin(
                2
                * np.pi
                * notes[idx]
                * tt
            )
        )

        fade = np.linspace(
            0,
            1,
            min(300, n),
            dtype=np.float32
        )

        if n > 600:
            tone[:300] *= fade
            tone[-300:] *= fade[::-1]

        wave_data[
            i:i + n
        ] += tone

    wave_data = np.clip(
        wave_data,
        -0.8,
        0.8
    )

    pcm = (
        wave_data * 32767
    ).astype(np.int16)

    safe_style = (
        style
        .split("/")[0]
        .strip()
        .replace(" ", "_")
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


def combine_videos(
    paths,
    output
):
    try:
        from moviepy import (
            VideoFileClip,
            concatenate_videoclips
        )
    except Exception:
        try:
            from moviepy.editor import (
                VideoFileClip,
                concatenate_videoclips
            )
        except Exception as exc:
            return (
                None,
                str(exc)
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
                "کوئی video clip موجود نہیں۔"
            )

        final = concatenate_videoclips(
            clips,
            method="compose"
        )

        final.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            logger=None
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
    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip
        )
    except Exception:
        try:
            from moviepy.editor import (
                VideoFileClip,
                AudioFileClip
            )
        except Exception as exc:
            return (
                None,
                str(exc)
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

        elif audio.duration < video.duration:
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
        else:
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
            logger=None
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
    "اردو + English | "
    "Story → Scenes → AI Images → "
    "AI Motion → Music → Movie"
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
            len(state["images"])
        )
    )

    st.write(
        "Motion: "
        + str(
            len(state["videos"])
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
    placeholder=(
        "مثال: ایک پیاسا کوا جنگل میں اڑ رہا تھا..."
    )
)


col1, col2, col3 = st.columns(3)


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
            "Cinematic"
        ]
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


a, b, c = st.columns(3)


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

        save_state(
            state
        )

        st.success(
            f"{len(state['scenes'])} scenes تیار ہو گئے۔"
        )


if state["scenes"]:

    st.subheader(
        "🎞️ Scene Plan"
    )

    for scene in state["scenes"]:

        st.markdown(
            f"**Scene {scene['number']}** — "
            f"{scene['story']}  \n"
            f"**Action:** "
            f"{scene['action']}"
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

        for index, scene in enumerate(
            state["scenes"],
            1
        ):

            key = str(
                scene["number"]
            )

            if (
                key not in state["images"]
                or not Path(
                    state["images"][key]
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

                state["images"][key] = path

                save_state(
                    state
                )

            progress.progress(
                index
                / len(state["scenes"])
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

        progress = st.progress(
            0
        )

        total = (
            len(state["scenes"])
            * clips_per_scene
        )

        done = 0

        for scene in state["scenes"]:

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

                if (
                    vkey in state["videos"]
                    and Path(
                        state["videos"][vkey]
                    ).exists()
                ):

                    done += 1

                    progress.progress(
                        done / total
                    )

                    continue

                path, error = create_ai_video(
                    image_path,
                    scene["action"],
                    scene["number"],
                    clip_no
                )

                if error:

                    st.error(
                        f"Scene {key}, "
                        f"clip {clip_no}: "
                        f"{error}"
                    )

                    st.info(
                        "Remote AI quota/queue ختم "
                        "ہونے پر بعد میں Resume سے "
                        "جاری کر سکتے ہیں۔"
                    )

                    save_state(
                        state
                    )

                    break

                state["videos"][vkey] = path

                save_state(
                    state
                )

                done += 1

                progress.progress(
                    done / total
                )

        st.success(
            "Motion process مکمل ہو گیا۔"
        )


st.divider()


if st.button(
    "🎬 Build Full Movie",
    use_container_width=True
):

    video_paths = []

    for scene in state["scenes"]:

        for clip_no in range(
            1,
            clips_per_scene + 1
        ):

            key = (
                f"{scene['number']}_{clip_no}"
            )

            if (
                key in state["videos"]
                and Path(
                    state["videos"][key]
                ).exists()
            ):

                video_paths.append(
                    state["videos"][key]
                )

    if not video_paths:

        st.warning(
            "پہلے AI M
