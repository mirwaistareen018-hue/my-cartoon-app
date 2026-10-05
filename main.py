import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave
import re
import numpy as np

st.set_page_config(page_title="AI Cartoon Movie Generator", layout="wide")

for key, default in {
    "scenes": [],
    "images": {},
    "videos": {},
    "full_movie": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

HF_TOKEN = st.secrets.get("HF_TOKEN", "")


def generate_image(prompt, scene_number):
    if not HF_TOKEN:
        return None, "HF_TOKEN نہیں ملا۔ Secrets میں ڈالیں۔"
    try:
        client = InferenceClient(
            model="black-forest-labs/FLUX.1-schnell",
            token=HF_TOKEN,
            provider="auto",
        )
        image = client.text_to_image(prompt)
        os.makedirs("images", exist_ok=True)
        path = f"images/scene_{scene_number}.png"
        image.save(path)
        return path, None
    except Exception as exc:
        return None, str(exc)


def create_ai_video(image_path, motion_prompt, scene_number, clip_number=1):
    temp_path = None
    try:
        from gradio_client import Client, handle_file

        if not image_path or not os.path.exists(image_path):
            return None, "Image file نہیں ملی۔"

        os.makedirs("videos", exist_ok=True)
        temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_path = temp.name
        temp.close()
        shutil.copyfile(image_path, temp_path)

        client = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster")

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

        generated = result[0] if isinstance(result, (list, tuple)) else result

        if not generated or not isinstance(generated, str):
            return None, "AI نے video file واپس نہیں کی۔"

        output = f"videos/scene_{scene_number}_clip_{clip_number}.mp4"
        shutil.copyfile(generated, output)
        return output, None

    except Exception as exc:
        return None, str(exc)

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def create_music(style, duration, output_path, volume=0.18, track=1):
    patterns = {
        "Happy / Cheerful": [261.63, 329.63, 392.00, 523.25],
        "Cute / Sweet": [392.00, 440.00, 523.25, 587.33],
        "Farm / Nature": [220.00, 261.63, 329.63, 392.00],
        "Magical / Fantasy": [523.25, 659.25, 783.99, 1046.50],
        "Funny Cartoon": [261.63, 329.63, 277.18, 369.99],
        "Peaceful": [261.63, 329.63, 392.00, 523.25],
        "Cinematic": [196.00, 246.94, 293.66, 392.00],
    }

    notes = list(patterns.get(style, patterns["Happy / Cheerful"]))

    if track == 2:
        notes = notes[1:] + notes[:1]
    elif track == 3:
        notes = list(reversed(notes))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    sample_rate = 22050
    duration = max(0.0, float(duration))
    total_samples = int(duration * sample_rate)

    if total_samples <= 0:
        return

    t = np.linspace(0, duration, total_samples, endpoint=False)
    freq_pattern = np.array(notes, dtype=float)
    freq_indices = (t * 2).astype(int) % len(freq_pattern)
    freqs = freq_pattern[freq_indices]

    wave_data = np.sin(2 * np.pi * freqs * t) * float(volume)
    wave_data = np.clip(wave_data, -1.0, 1.0)
    wave_data = (wave_data * 32767).astype(np.int16)

    with wave.open(output_path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(wave_data.tobytes())


def split_story(story, count):
    parts = re.split(r"(?<=[.!?۔])\s+|\n+", story.strip())
    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        return []

    if len(parts) <= count:
        return parts

    size = math.ceil(len(parts) / count)
    return [
        " ".join(parts[i:i + size])
        for i in range(0, len(parts), size)
    ][:count]


def character_description(story):
    text = story.lower()

    if "crow" in text or "کوا" in text:
        return "a cute cartoon crow with black feathers, expressive eyes and orange beak"

    if "rabbit" in text or "خرگوش" in text:
        return "a cute cartoon rabbit with soft white fur and expressive eyes"

    if "fox" in text or "لومڑی" in text:
        return "a cute cartoon fox with orange fur and expressive eyes"

    return "a cute colorful cartoon main character with expressive eyes"


def detect_action(text):
    lower = text.lower()

    if any(w in lower for w in ["fly", "flies", "اڑ", "اڑتا", "اڑتی"]):
        return "flies smoothly through the scene"

    if any(w in lower for w in ["stone", "stones", "پتھر"]):
        return "picks up small stones and drops them carefully"

    if any(w in lower for w in ["water", "پانی"]):
        return "moves toward the water and drinks happily"

    if any(w in lower for w in ["pot", "مٹکا", "گھڑا"]):
        return "walks toward the pot and looks inside"

    if any(w in lower for w in ["drink", "drinks", "پیتا", "پیتی", "پینا"]):
        return "drinks happily"

    if any(w in lower for w in ["run", "runs", "دوڑ", "دوڑتا", "دوڑتی"]):
        return "runs naturally through the scene"

    if any(w in lower for w in ["walk", "walks", "چل", "چلتا", "چلتی"]):
        return "walks naturally through the scene"

    return "moves naturally with subtle cinematic motion"


def make_scene_plan(story, count):
    pieces = split_story(story, count)
    character = character_description(story)
    scenes = []

    for number, text in enumerate(pieces, 1):
        scenes.append(
            {
                "number": number,
                "story": text,
                "image_prompt": (
                    "high quality 3D cartoon movie frame, "
                    + character
                    + ", beautiful cinematic environment, "
                    + "colorful family friendly animation, "
                    + "consistent character design, story moment: "
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


def combine_clips(paths, output_path, target_duration):
    clips = []
    final = None

    try:
        from moviepy import VideoFileClip, concatenate_videoclips

        valid = [
            p for p in paths
            if p and os.path.exists(p)
        ]

        if not valid:
            return None, "کوئی video clips نہیں ملیں۔"

        clips = [VideoFileClip(p) for p in valid]

        total = sum(float(c.duration or 0) for c in clips)

        if total <= 0:
            return None, "Video duration صفر ہے۔"

        target_duration = max(1.0, float(target_duration))
        repeats = max(1, math.ceil(target_duration / total))

        final = concatenate_videoclips(
            clips * repeats,
            method="compose",
        )

        if final.duration > target_duration:
            final = final.subclipped(0, target_duration)

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        return output_path, None

    except Exception as exc:
        return None, str(exc)

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


def add_full_music(video_path, style, track, volume):
    video = None
    audio = None
    final = None

    try:
        from moviepy import VideoFileClip, AudioFileClip

        if not video_path or not os.path.exists(video_path):
            return None, "Silent movie file نہیں ملی۔"

        video = VideoFileClip(video_path)

        music_path = "music/full_movie.wav"

        create_music(
            style,
            float(video.duration),
            music_path,
            volume,
            track,
        )

        audio = AudioFileClip(music_path)
        final = video.with_audio(audio)

        output = "final_cartoon_movie.mp4"

        final.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        return output, None

    except Exception as exc:
        return None, str(exc)

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

    total_steps = len(scenes) * (1 + clips_per_scene) + 2
    done = 0

    for scene in scenes:
        number = scene["number"]

        status.write(
            f"🖼️ Scene {number}: AI image..."
        )

        image_path = st.session_state.images.get(number)

        if not image_path or not os.path.exists(image_path):
            image_path, error = generate_image(
                scene["image_prompt"],
                number,
            )

            if error:
                return None, error

            st.session_state.images[number] = image_path

        done += 1
        progress.progress(
            min(1.0, done / total_steps)
        )

        for clip_no in range(1, clips_per_scene + 1):
            status.write(
                f"🎥 Scene {number}: AI motion {clip_no}..."
            )

            key = f"{number}_{clip_no}"
            video_path = st.session_state.videos.get(key)

            if not video_path or not os.path.exists(video_path):
                video_path, error = create_ai_video(
                    image_path,
                    scene["motion_prompt"],
                    number,
                    clip_no,
                )

                if error:
                    return None, error

                st.session_state.videos[key] = video_path

            all_clips.append(video_path)

            done += 1
            progress.progress(
                min(1.0, done / total_steps)
            )

    status.write(
        "✂️ Clips کو جوڑا جا رہا ہے..."
    )

    silent_movie, error = combine_clips(
        all_clips,
        "full_movie_silent.mp4",
        duration_minutes * 60,
    )

    if error:
        return None, error

    done += 1
    progress.progress(
        min(1.0, done / total_steps)
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
        return None, error

    progress.progress(1.0)
    status.write(
        "✅ Final movie تیار ہے۔"
    )

    return final_movie, None


st.title(
    "🎬 AI Cartoon Movie Generator"
)

story = st.text_area(
    "📝 Full Story / Script",
    height=220,
    placeholder="اپنی کہانی یہاں لکھیں...",
)

duration = st.selectbox(
    "⏱️ Movie Duration",
    [2, 3, 4, 5],
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

music_track = st.selectbox(
    "🎼 Music Variation",
    [1, 2, 3],
)

music_volume = st.slider(
    "🔊 Music Volume",
    0.05,
    0.35,
    0.18,
    0.01,
)

clips_per_scene = st.selectbox(
    "🎥 AI Clips per Scene",
    [1, 2, 3],
    index=1,
)


if st.button(
    "🧠 Create Cartoon Movie Project",
    use_container_width=True,
):
    if not story.strip():
        st.warning(
            "پہلے story لکھیں۔"
        )
    else:
        st.session_state.scenes = make_scene_plan(
            story,
            duration * 4,
        )

        st.session_state.images = {}
        st.session_state.videos = {}
        st.session_state.full_movie = None

        st.success(
            f"{len(st.session_state.scenes)} scenes تیار ہیں۔"
        )


if st.session_state.scenes:
    st.divider()
    st.header("🎭 Scene Plan")

    for scene in st.session_state.scenes:
        number = scene["number"]

        st.subheader(
            f"Scene {number}"
        )

        st.write(
            scene["story"]
        )

        st.caption(
            "🎬 " + scene["motion_prompt"]
        )

        if st.button(
            f"🖼️ Generate Image {number}",
            key=f"image_btn_{number}",
        ):
            with st.spinner(
                "Image بن رہی ہے..."
            ):
                path, error = generate_image(
                    scene["image_prompt"],
                    number,
                )

                if error:
                    st.error(error)
                else:
                    st.session_state.images[number] = path
                    st.success(
                        "Image تیار ہے۔"
                    )

        image_path = st.session_state.images.get(number)

        if image_path and os.path.exists(image_path):
            st.image(
                image_path,
                use_container_width=True,
            )

            if st.button(
                f"🎥 Animate Scene {number}",
                key=f"animate_btn_{number}",
            ):
                with st.spinner(
                    "AI video بن رہی ہے..."
                ):
                    path, error = create_ai_video(
                        image_path,
                        scene["motion_prompt"],
                        number,
                        1,
                    )

                    if error:
                        st.error(error)
                    else:
                        st.session_state.videos[
                            f"{number}_1"
                        ] = path

                        st.success(
                            "Video تیار ہے۔"
                        )

                        st.video(path)

    st.divider()

    if st.button(
        "🎬 پوری فلم بنائیں (Final Movie)",
        use_container_width=True,
        type="primary",
    ):
        progress = st.progress(0)
        status = st.empty()

        final_path, error = build_movie(
            st.session_state.scenes,
            duration,
            clips_per_scene,
            music_style,
            music_track,
            music_volume,
            progress,
            status,
        )

        if error:
            st.error(error)

        else:
            st.session_state.full_movie = final_path

            st.success(
                "فلم تیار ہے!"
            )

            st.video(
                final_path
            )

            with open(
                final_path,
                "rb",
            ) as file:
                st.download_button(
                    "⬇️ Download Final Movie",
                    file,
                    file_name="final_cartoon_movie.mp4",
                    mime="video/mp4",
            )
