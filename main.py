import streamlit as st
from huggingface_hub import InferenceClient
import os
import shutil
import tempfile
import math
import wave
import re

st.set_page_config(
    page_title="AI Cartoon Movie Studio",
    page_icon="🎬",
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================

if "scenes" not in st.session_state:
    st.session_state.scenes = []

if "generated_images" not in st.session_state:
    st.session_state.generated_images = {}

if "video_files" not in st.session_state:
    st.session_state.video_files = {}

if "final_videos" not in st.session_state:
    st.session_state.final_videos = {}

if "full_movie_path" not in st.session_state:
    st.session_state.full_movie_path = None

if "project_created" not in st.session_state:
    st.session_state.project_created = False


# =========================================================
# AI IMAGE GENERATION
# =========================================================

def generate_image(prompt):

    token = st.secrets.get("HF_TOKEN")

    if not token:
        return None, "HF_TOKEN نہیں ملا۔ Streamlit Secrets میں HF_TOKEN چیک کریں۔"

    try:

        client = InferenceClient(
            api_key=token,
            provider="auto"
        )

        image = client.text_to_image(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )

        return image, None

    except Exception as exc:

        return None, str(exc)


# =========================================================
# AI IMAGE TO VIDEO
# =========================================================

def create_ai_video(
    image,
    motion_prompt,
    scene_number,
    clip_number=1
):

    temp_path = None

    try:

        from gradio_client import Client, handle_file

        os.makedirs(
            "videos",
            exist_ok=True
        )

        temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        )

        temp_path = temp.name
        temp.close()

        image.save(temp_path)

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

        negative_prompt = (
            "static image, frozen frame, no movement, "
            + "blurry, distorted, deformed character, "
            + "extra limbs, flickering, unstable face, "
            + "warped body, bad anatomy"
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
            api_name="/generate_video"
        )

        if isinstance(result, (list, tuple)):
            generated = result[0]
        else:
            generated = result

        if not generated:
            return None, "AI نے video file واپس نہیں کی۔"

        output = (
            f"videos/scene_{scene_number}"
            f"_clip_{clip_number}.mp4"
        )

        if isinstance(generated, str):

            shutil.copyfile(
                generated,
                output
            )

        else:

            return None, (
                "AI video response کا format "
                "سمجھ نہیں آیا۔"
            )

        return output, None

    except Exception as exc:

        return None, str(exc)

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:
                os.remove(temp_path)
            except Exception:
                pass


# =========================================================
# BACKGROUND MUSIC
# =========================================================

def create_background_music(
    style,
    duration,
    output_path,
    volume,
    track=1
):

    sample_rate = 22050

    duration = max(
        1.0,
        float(duration)
    )

    patterns = {

        "😊 Happy / Cheerful": [

            [
                261.63,
                329.63,
                392.00,
                523.25
            ],

            [
                293.66,
                349.23,
                440.00,
                587.33
            ],

            [
                261.63,
                349.23,
                392.00,
                523.25
            ]

        ],

        "🌸 Cute / Sweet": [

            [
                261.63,
                293.66,
                329.63,
                392.00
            ],

            [
                293.66,
                329.63,
                392.00,
                440.00
            ],

            [
                261.63,
                329.63,
                392.00,
                493.88
            ]

        ],

        "🌾 Farm / Nature": [

            [
                220.00,
                261.63,
                329.63,
                392.00
            ],

            [
                246.94,
                293.66,
                369.99,
                440.00
            ],

            [
                220.00,
                293.66,
                329.63,
                440.00
            ]

        ],

        "✨ Magical / Fantasy": [

            [
                261.63,
                349.23,
                440.00,
                523.25
            ],

            [
                293.66,
                369.99,
                466.16,
                587.33
            ],

            [
                261.63,
                329.63,
                392.00,
                523.25
            ]

        ],

        "😂 Funny Cartoon": [

            [
                293.66,
                369.99,
                440.00,
                587.33
            ],

            [
                329.63,
                415.30,
                493.88,
                659.25
            ],

            [
                293.66,
                392.00,
                466.16,
                587.33
            ]

        ],

        "😌 Peaceful": [

            [
                220.00,
                261.63,
                329.63,
                392.00
            ],

            [
                196.00,
                246.94,
                293.66,
                369.99
            ],

            [
                220.00,
                277.18,
                329.63,
                415.30
            ]

        ],

        "🎬 Cinematic": [

            [
                196.00,
                246.94,
                293.66,
                392.00
            ],

            [
                220.00,
                277.18,
                349.23,
                440.00
            ],

            [
                196.00,
                293.66,
                349.23,
                392.00
            ]

        ]

    }

    selected = patterns.get(
        style,
        patterns["😊 Happy / Cheerful"]
    )

    offset = (
        int(track) - 1
    ) % len(selected)

    selected = (
        selected[offset:]
        + selected[:offset]
    )

    total_samples = int(
        duration * sample_rate
    )

    chunk_size = sample_rate

    with wave.open(
        output_path,
        "wb"
    ) as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        start = 0

        while start < total_samples:

            end = min(
                start + chunk_size,
                total_samples
            )

            frames = []

            for i in range(
                start,
                end
            ):

                current_time = (
                    i / sample_rate
                )

                section = (
                    int(
                        current_time / 8.0
                    )
                    % len(selected)
                )

                pattern = selected[
                    section
                ]

                note_index = (
                    int(
                        (current_time % 2.0)
                        / 0.5
                    )
                    % len(pattern)
                )

                frequency = pattern[
                    note_index
                ]

                melody = math.sin(
                    2
                    * math.pi
                    * frequency
                    * current_time
                )

                harmony = (
                    0.22
                    * math.sin(
                        2
                        * math.pi
                        * frequency
                        * 1.5
                        * current_time
                    )
                )

                bass = (
                    0.10
                    * math.sin(
                        2
                        * math.pi
                        * (frequency / 2)
                        * current_time
                    )
                )

                fade_in = min(
                    1.0,
                    current_time / 1.5
                )

                remaining = (
                    duration
                    - current_time
                )

                fade_out = min(
                    1.0,
                    max(
                        0.0,
                        remaining / 2.0
                    )
                )

                envelope = min(
                    fade_in,
                    fade_out
                )

                sample = (
                    melody
                    + harmony
                    + bass
                )

                sample = (
                    sample
                    * volume
                    * envelope
                )

                sample = max(
                    -1.0,
                    min(
                        1.0,
                        sample
                    )
                )

                value = int(
                    sample * 32767
                )

                frames.append(
                    value.to_bytes(
                        2,
                        "little",
                        signed=True
                    )
                )

            wav.writeframes(
                b"".join(frames)
            )

            start = end

    return output_path


# =========================================================
# MUSIC ON SINGLE SCENE
# =========================================================

def add_music_to_video(
    video_path,
    style,
    scene_number,
    volume,
    track=1
):

    try:

        from moviepy import (
            VideoFileClip,
            AudioFileClip
        )

        os.makedirs(
            "music",
            exist_ok=True
        )

        os.makedirs(
            "final_videos",
            exist_ok=True
        )

        music_path = (
            f"music/scene_{scene_number}.wav"
        )

        final_path = (
            f"final_videos/"
            f"scene_{scene_number}_final.mp4"
        )

        video = VideoFileClip(
            video_path
        )

        create_background_music(
            style,
            video.duration,
            music_path,
            volume,
            track
        )

        audio = AudioFileClip(
            music_path
        )

        final_video = video.with_audio(
            audio
        )

        final_video.write_videofile(
            final_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            logger=None
        )

        final_video.close()
        audio.close()
        video.close()

        return final_path, None

    except Exception as exc:

        return None, str(exc)


# =========================================================
# STORY SPLITTER
# =========================================================

def split_story(
    story,
    count
):

    story = story.strip()

    if not story:
        return []

    parts = re.split(
        r"(?<=[.!?۔؟!])\s+|\n+",
        story
    )

    parts = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    if not parts:
        return [
            story
        ]

    if len(parts) <= count:
        return parts

    groups = []

    base = (
        len(parts)
        // count
    )

    extra = (
        len(parts)
        % count
    )

    index = 0

    for i in range(
        count
    ):

        size = (
            base
            + (
                1
                if i < extra
                else 0
            )
        )

        text = " ".join(
            parts[
                index:index + size
            ]
        )

        if text:
            groups.append(
                text
            )

        index += size

    return groups


# =========================================================
# ACTION DETECTION
# =========================================================

def detect_action(
    text
):

    lower = text.lower()

    if any(
        x in lower
        for x in [
            "fly",
            "flies",
            "flying",
            "اڑ",
            "اڑا",
            "اڑتا",
            "उड़",
            "उड़ा"
        ]
    ):

        return (
            "The character flies naturally, "
            "moves its wings, looks around, "
            "and changes direction gently."
        )

    if any(
        x in lower
        for x in [
            "stone",
            "stones",
            "پتھر",
            "पत्थर"
        ]
    ):

        return (
            "The character notices small stones, "
            "moves toward them, picks them up, "
            "and interacts with them naturally."
        )

    if any(
        x in lower
        for x in [
            "water",
            "drink",
            "drinks",
            "پانی",
            "پیتا",
            "پینا",
            "पानी",
            "पीता",
            "पीना"
        ]
    ):

        return (
            "The character approaches the water, "
            "looks at it, leans forward naturally, "
            "and drinks happily."
        )

    if any(
        x in lower
        for x in [
            "pot",
            "matka",
            "مٹکا",
            "گھڑا",
            "घड़ा",
            "मटका"
        ]
    ):

        return (
            "The character notices an earthen pot, "
            "approaches it, looks inside curiously, "
            "and reacts naturally."
        )

    if any(
        x in lower
        for x in [
            "run",
            "runs",
            "running",
            "دوڑ",
            "दौड़"
        ]
    ):

        return (
            "The character runs naturally through "
            "the environment with believable "
            "body and leg movement."
        )

    if any(
        x in lower
        for x in [
            "walk",
            "walks",
            "walking",
            "چل",
            "چلتا",
            "चल",
            "चलता"
        ]
    ):

        return (
            "The character walks naturally, "
            "looks around, and interacts "
            "with the environment."
        )

    if any(
        x in lower
        for x in [
            "look",
            "looks",
            "see",
            "sees",
            "دیکھ",
            "देख"
        ]
    ):

        return (
            "The character looks around slowly, "
            "notices the important object, "
            "and reacts with expressive "
            "facial movement."
        )

    if any(
        x in lower
        for x in [
            "happy",
            "happily",
            "خوش",
            "खुश"
        ]
    ):

        return (
            "The character becomes happy, "
            "smiles, and shows joyful "
            "natural body language."
        )

    if any(
        x in lower
        for x in [
            "sad",
            "اداس",
            "उदास"
        ]
    ):

        return (
            "The character shows gentle sadness "
            "with natural facial expression "
            "and slow movement."
        )

    return (
        "Characters perform the story action "
        "naturally with walking, looking, "
        "turning, object interaction, and "
        "expressive body movement."
    )


# =========================================================
# CHARACTER DESCRIPTION
# =========================================================

def character_description(
    story
):

    lower = story.lower()

    if any(
        x in lower
        for x in [
            "crow",
            "کوا",
            "कौआ"
        ]
    ):

        return (
            "a cute black crow with expressive eyes, "
            "soft cartoon feathers, and a friendly "
            "child-safe design"
        )

    if any(
        x in lower
        for x in [
            "rabbit",
            "خرگوش",
            "खरगोश"
        ]
    ):

        return (
            "a cute fluffy rabbit with expressive eyes "
            "and a friendly child-safe cartoon design"
        )

    if any(
        x in lower
        for x in [
            "fox",
            "لومڑی",
            "लोमड़ी"
        ]
    ):

        return (
            "a friendly orange fox with expressive eyes "
            "and a child-safe cartoon design"
        )

    return (
        "friendly expressive cartoon characters "
        "with consistent appearance"
    )


# =========================================================
# STORY PLAN
# =========================================================

def create_scene_plan(
    story,
    count,
    language
):

    parts = split_story(
        story,
        count
    )

    character = character_description(
        story
    )

    scenes = []

    for number, part in enumerate(
        parts,
        start=1
    ):

        action = detect_action(
            part
        )

        if language == "اردو":

            story_text = (
                f"{part} — منظر {number}"
            )

        else:

            story_text = (
                f"{part} — Scene {number}"
            )

        image_prompt = (
            "2D colorful children's cartoon, "
            "beautiful cinematic environment, "
            "friendly expressive characters, "
            "consistent character design, "
            "child-safe animation style, "
            f"main character: {character}, "
            f"story action: {part}, "
            "clear composition, high quality, "
            "same visual world and character appearance"
        )

        animation_prompt = (
            action
            + " Keep the main character appearance "
            + "consistent. Use natural movement and "
            + "gentle cinematic camera movement."
        )

        scenes.append({
            "scene": number,
            "story": story_text,
            "character": character,
            "image_prompt": image_prompt,
            "animation_prompt": animation_prompt
        })

    return scenes


# =========================================================
# JOIN VIDEO CLIPS
# =========================================================

def combine_video_clips(
    video_paths,
    output_path,
    target_duration
):

    from moviepy import (
        VideoFileClip,
        concatenate_videoclips
    )

    clips = []
    final_video = None

    try:

        for path in video_paths:

            if (
                path
                and os.path.exists(path)
            ):

                clips.append(
                    VideoFileClip(path)
    
