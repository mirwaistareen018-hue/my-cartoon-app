import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave
import re

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
        return None, "HF_TOKEN نہیں ملا۔"

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


def create_ai_video(
    image_path,
    motion_prompt,
    scene_number,
    clip_number=1,
):
    temp_path = None

    try:
        from gradio_client import Client, handle_file

        os.makedirs("videos", exist_ok=True)

        temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )

        temp_path = temp.name
        temp.close()

        shutil.copyfile(
            image_path,
            temp_path,
        )

        client = Client(
            "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
        )

        prompt = (
            motion_prompt
            + ", smooth natural movement, natural body movement, "
            + "natural environmental movement, cinematic camera movement, "
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

        if isinstance(result, (list, tuple)):
            generated = result[0]
        else:
            generated = result

        if not generated:
            return None, "AI نے video file واپس نہیں کی۔"

        if not isinstance(generated, str):
            return None, "AI video response کا format سمجھ نہیں آیا۔"

        output = (
            f"videos/scene_{scene_number}"
            f"_clip_{clip_number}.mp4"
        )

        shutil.copyfile(
            generated,
            output,
        )

        return output, None

    except Exception as exc:
        return None, str(exc)

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def create_music(
    style,
    duration,
    output_path,
    volume=0.18,
    track=1,
):
    patterns = {
        "Happy / Cheerful": [
            [261.63, 329.63, 392.00, 329.63],
            [293.66, 349.23, 440.00, 349.23],
            [329.63, 392.00, 493.88, 392.00],
        ],
        "Cute / Sweet": [
            [392.00, 440.00, 523.25, 440.00],
            [349.23, 392.00, 493.88, 392.00],
            [440.00, 493.88, 587.33, 493.88],
        ],
        "Farm / Nature": [
            [220.00, 261.63, 329.63, 261.63],
            [196.00, 246.94, 293.66, 246.94],
            [246.94, 293.66, 369.99, 293.66],
        ],
        "Magical / Fantasy": [
            [523.25, 659.25, 783.99, 659.25],
            [493.88, 622.25, 739.99, 622.25],
            [587.33, 739.99, 880.00, 739.99],
        ],
        "Funny Cartoon": [
            [261.63, 329.63, 277.18, 369.99],
            [293.66, 369.99, 311.13, 415.30],
            [329.63, 415.30, 349.23, 440.00],
        ],
        "Peaceful": [
            [261.63, 329.63, 392.00, 523.25],
            [293.66, 349.23, 440.00, 587.33],
            [246.94, 329.63, 392.00, 493.88],
        ],
        "Cinematic": [
            [196.00, 246.94, 293.66, 392.00],
            [220.00, 277.18, 329.63, 440.00],
            [246.94, 311.13, 369.99, 493.88],
        ],
    }

    pattern_list = patterns.get(
        style,
        patterns["Happy / Cheerful"],
    )

    pattern = pattern_list[
        (track - 1) % len(pattern_list)
    ]

    os.makedirs(
        os.path.dirname(output_path) or ".",
        exist_ok=True,
    )

    sample_rate = 22050

    total_samples = int(
        max(0, duration) * sample_rate
    )

    with wave.open(
        output_path,
        "w",
    ) as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for start in range(
            0,
            total_samples,
            sample_rate,
        ):
            end = min(
                start + sample_rate,
                total_samples,
            )

            frames = []

            for sample_index in range(
                start,
                end,
            ):
                time_value = (
                    sample_index / sample_rate
                )

                note = pattern[
                    int(time_value / 0.5)
                    % len(pattern)
                ]

                value = (
                    math.sin(
                        2
                        * math.pi
                        * note
                        * time_value
                    )
                    * volume
                )

                value += (
                    math.sin(
                        2
                        * math.pi
                        * note
                        * 2
                        * time_value
                    )
                    * volume
                    * 0.25
                )

                value = max(
                    -1.0,
                    min(1.0, value),
                )

                frames.append(
                    int(
                        value * 32767
                    ).to_bytes(
                        2,
                        "little",
                        signed=True,
                    )
                )

            wav.writeframes(
                b"".join(frames)
            )


def split_story(story, count):
    parts = re.split(
        r"(?<=[.!?۔])\s+|\n+",
        story.strip(),
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if not parts:
        return []

    if len(parts) <= count:
        return parts

    size = math.ceil(
        len(parts) / count
    )

    result = []

    for index in range(
        0,
        len(parts),
        size,
    ):
        result.append(
            " ".join(
                parts[
                    index:index + size
                ]
            )
        )

    return result[:count]


def character_description(story):
    text = story.lower()

    if (
        "crow" in text
        or "کوا" in text
        or "کوّا" in text
    ):
        return (
            "a cute cartoon crow with black feathers, "
            "expressive eyes and orange beak"
        )

    if (
        "rabbit" in text
        or "خرگوش" in text
    ):
        return (
            "a cute cartoon rabbit with soft white fur "
            "and expressive eyes"
        )

    if (
        "fox" in text
        or "لومڑی" in text
    ):
        return (
            "a cute cartoon fox with orange fur "
            "and expressive eyes"
        )

    return (
        "a cute colorful cartoon main character "
        "with expressive eyes"
    )


def detect_action(text):
    lower = text.lower()

    if any(
        word in lower
        for word in [
            "fly",
            "flies",
            "flying",
            "اڑ",
            "اڑتا",
            "اڑتی",
        ]
    ):
        return (
            "flies smoothly through the environment"
        )

    if any(
        word in lower
        for word in [
            "stone",
            "stones",
            "pebble",
            "پتھر",
            "کنکر",
        ]
    ):
        return (
            "picks up small stones "
            "and drops them carefully"
        )

    if any(
        word in lower
        for word in [
            "water",
            "drink",
            "drinks",
            "پانی",
            "پیتا",
            "پیتی",
        ]
    ):
        return (
            "drinks water happily"
        )

    if any(
        word in lower
        for word in [
            "pot",
            "مٹکا",
            "گھڑا",
            "برتن",
        ]
    ):
        return (
            "walks toward the pot "
            "and looks inside"
        )

    if any(
        word in lower
        for word in [
            "run",
            "runs",
            "running",
            "دوڑ",
        ]
    ):
        return (
            "runs naturally through the scene"
        )

    if any(
        word in lower
        for word in [
            "walk",
            "walks",
            "walking",
            "چلتا",
            "چلتی",
        ]
    ):
        return (
            "walks naturally through the scene"
        )

    if any(
        word in lower
        for word in [
            "look",
            "looks",
            "see",
            "sees",
            "دیکھ",
        ]
    ):
        return (
            "looks around and reacts naturally"
        )

    if any(
        word in lower
        for word in [
            "happy",
            "happily",
            "خوش",
            "مسکرا",
        ]
    ):
        return (
            "becomes happy and moves cheerfully"
        )

    return (
        "moves naturally with subtle "
        "body and environmental motion"
    )


def make_scene_plan(story, count):
    pieces = split_story(
        story,
        count,
    )

    character = character_description(
        story
    )

    scenes = []

    for number, text in enumerate(
        pieces,
        1,
    ):
        action = detect_action(
            text
        )

        image_prompt = (
            "high quality 3D cartoon movie frame, "
            + character
            + ", beautiful cinematic environment, "
            + "colorful family friendly animation, "
            + "soft lighting, consistent character design, "
            + "story moment: "
            + text
        )

        motion_prompt = (
            action
            + ", story moment: "
            + text
        )

        scenes.append(
            {
                "number": number,
                "story": text,
                "image_prompt": image_prompt,
                "motion_prompt": motion_prompt,
            }
        )

    return scenes


def combine_clips(
    paths,
    output_path,
    target_duration,
):
    try:
        from moviepy import (
            VideoFileClip,
            concatenate_videoclips,
        )

        valid = [
            path
            for path in paths
            if path
            and os.path.exists(path)
        ]

        if not valid:
            return None, (
                "کوئی video clips نہیں ملیں۔"
            )

        source = [
            VideoFileClip(path)
            for path in valid
        ]

        total = sum(
            float(clip.duration)
            for clip in source
        )

        if total <= 0:
            for clip in source:
                clip.close()

            return None, (
                "Video duration صفر ہے۔"
            )

        repeats = max(
            1,
            math.ceil(
                target_duration / total
            ),
        )

        selected = source * repeats

        final = concatenate_videoclips(
            selected,
            method="compose",
        )

        if final.duration > target_duration:
            trimmed = final.subclipped(
                0,
                target_duration,
            )

            final.close()
            final = trimmed

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        final.close()

        for clip in source:
            clip.close()

        return output_path, None

    except Exception as exc:
        return None, str(exc)


def add_full_music(
    video_path,
    style,
    track,
    volume,
):
    try:
        from moviepy import (
            VideoFileClip,
            AudioFileClip,
        )

        video = VideoFileClip(
            video_path
        )

        music_path = (
            "music/full_movie.wav"
        )

        create_music(
            style,
            float(video.duration),
            music_path,
            volume,
            track,
        )

        audio = AudioFileClip(
            music_path
        )

        final = video.with_audio(
            audio
        )

        output = (
            "final_cartoon_movie.mp4"
        )

        final.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None,
        )

        final.close()
        audio.close()
        video.close()

        return output, None

    except Exception as exc:
        return None, str(exc)


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

    total_steps = max(
        1,
        len(scenes)
        * (1 + clips_per_scene)
        + 2,
    )

    done = 0

    for scene in scenes:
        number = scene["number"]

        status.write(
            f"🖼️ Scene {number}: AI image..."
        )

        image_path = (
            st.session_state.images.get(
                number
            )
        )

        if (
            not image_path
            or not os.path.exists(
                image_path
            )
        ):
            image_path, error = (
                generate_image(
                    scene["image_prompt"],
                    number,
                )
            )

            if error:
                return None, error

            st.session_state.images[
                number
            ] = image_path

        done += 1

        progress.progress(
            min(
                1.0,
                done / total_steps,
            )
        )

        for clip_no in range(
            1,
            clips_per_scene + 1,
        ):
            status.write(
                f"🎥 Scene {number}: "
                f"AI motion {clip_no}..."
            )

            key = f"{number}_{clip_no}"

            video_path = (
                st.session_state.videos.get(
                    key
                )
            )

            if (
                not video_path
                or not os.path.exists(
                    video_path
                )
            ):
                video_path, error = (
                    create_ai_video(
                        image_path,
                        scene["motion_prompt"],
                        number,
                        clip_no,
                    )
                )

                if error:
                    return None, error

                st.session_state.videos[
                    key
                ] = video_path

            all_clips.append(
                video_path
            )

            done += 1

            progress.progress(
                min(
                    1.0,
                    done / total_steps,
                )
            )

    status.write(
        "✂️ Clips کو ایک movie میں "
        "جوڑا جا رہا ہے..."
    )

    silent_movie, error = (
        combine_clips(
            all_clips,
            "full_movie_silent.mp4",
            duration_minutes * 60,
        )
    )

    if error:
        return None, error

    done += 1

    progress.progress(
        min(
            1.0,
            done / total_steps,
        )
    )

    status.write(
        "🎵 پوری movie کے لیے "
        "music بن رہی ہے..."
    )

    final_movie, error = (
        add_full_music(
            silent_movie,
            music_style,
            music_track,
            music_volume,
        )
    )

    if error:
        return None, error

    progress.progress(1.0)

    return final_movie, None


st.title(
    "🎬 AI Cartoon Movie Generator"
)

st.write(
    "Story → Scenes → AI Images → "
    "AI Motion → Continuous Music → Final MP4"
)

language = st.selectbox(
    "🌐 Language",
    [
        "English",
        "Urdu",
        "Hindi",
    ],
)

story = st.text_area(
    "📝 Full Story / Script",
    height=220,
    placeholder=(
        "اپنی پوری کہانی یہاں paste کریں..."
    ),
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
        st.session_state.scenes = (
            make_scene_plan(
                story,
                duration * 4,
            )
        )

        st.session_state.images = {}
        st.session_state.videos = {}
        st.session_state.full_movie = None

        st.success(
            f"{len(st.session_state.scenes)} "
            "scenes تیار ہیں۔"
        )


if st.session_state.scenes:
    st.divider()

    st.header(
        "🎭 Scene Plan"
    )

    for scene in st.session_state.scenes:
        number = scene["number"]

        st.subheader(
            f"Scene {number}"
        )

        st.write(
            scene["story"]
        )

        st.caption(
            "🎬 "
            + scene["motion_prompt"]
        )

        if st.button(
            f"🖼️ Generate Image {number}",
            key=f"image_btn_{number}",
        ):
            path, error = (
                generate_image(
                    scene["image_prompt"],
                    number,
                )
            )

            if error:
                st.error(error)

            else:
                st.session_state.images[
                    number
                ] = path

                st.success(
                    "Image تیار ہے۔"
                )

        image_path = (
            st.session_state.images.get(
                number
            )
        )

        if (
            image_path
            and os.path.exists(
                image_path
            )
        ):
            st.image(
                image_path,
                use_container_width=True,
            )

            if st.button(
                f"🎥 Animate Scene {number}",
                key=f"animate_btn_{number}",
            ):
                path, error = (
                    create_ai_video(
                        image_path,
                        scene["motion_prompt"],
                        number,
                        1,
                    )
                )

                if error:
                    st.error(error)

                else:
                    st.session_state.videos[
                        f"{number}_1"
           
