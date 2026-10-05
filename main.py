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

DEFAULTS = {
    "scenes": [],
    "generated_images": {},
    "video_files": {},
    "final_videos": {},
    "full_movie_path": None,
    "project_created": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        if isinstance(value, dict):
            st.session_state[key] = {}
        elif isinstance(value, list):
            st.session_state[key] = []
        else:
            st.session_state[key] = value


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

        try:
            os.remove(temp_path)
        except Exception:
            pass

        return output, None

    except Exception as exc:

        return None, str(exc)


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

    music_patterns = {

        "😊 Happy / Cheerful": [

            [261.63, 329.63, 392.00, 523.25],

            [293.66, 349.23, 440.00, 587.33],

            [261.63, 349.23, 392.00, 523.25]

        ],

        "🌸 Cute / Sweet": [

            [261.63, 293.66, 329.63, 392.00],

            [293.66, 329.63, 392.00, 440.00],

            [261.63, 329.63, 392.00, 493.88]

        ],

        "🌾 Farm / Nature": [

            [220.00, 261.63, 329.63, 392.00],

            [246.94, 293.66, 369.99, 440.00],

            [220.00, 293.66, 329.63, 440.00]

        ],

        "✨ Magical / Fantasy": [

            [261.63, 349.23, 440.00, 523.25],

            [293.66, 369.99, 466.16, 587.33],

            [261.63, 329.63, 392.00, 523.25]

        ],

        "😂 Funny Cartoon": [

            [293.66, 369.99, 440.00, 587.33],

            [329.63, 415.30, 493.88, 659.25],

            [293.66, 392.00, 466.16, 587.33]

        ],

        "😌 Peaceful": [

            [220.00, 261.63, 329.63, 392.00],

            [196.00, 246.94, 293.66, 369.99],

            [220.00, 277.18, 329.63, 415.30]

        ],

        "🎬 Cinematic": [

            [196.00, 246.94, 293.66, 392.00],

            [220.00, 277.18, 349.23, 440.00],

            [196.00, 293.66, 349.23, 392.00]

        ]

    }

    style_patterns = music_patterns.get(
        style,
        music_patterns["😊 Happy / Cheerful"]
    )

    shift = max(
        0,
        int(track) - 1
    )

    shift = shift % len(style_patterns)

    selected_patterns = (
        style_patterns[shift:]
        + style_patterns[:shift]
    )

    with wave.open(
        output_path,
        "wb"
    ) as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        chunk_seconds = 1.0

        total_samples = int(
            duration * sample_rate
        )

        chunk_size = int(
            chunk_seconds * sample_rate
        )

        position = 0

        while position < total_samples:

            end = min(
                position + chunk_size,
                total_samples
            )

            frames = []

            for i in range(
                position,
                end
            ):

                current_time = (
                    i / sample_rate
                )

                section = int(
                    current_time / 8.0
                )

                pattern = selected_patterns[
                    section
                    % len(selected_patterns)
                ]

                beat_time = (
                    current_time % 2.0
                )

                note_index = (
                    int(beat_time / 0.5)
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

                frames.append(
                    int(
                        sample * 32767
                    ).to_bytes(
                        2,
                        byteorder="little",
                        signed=True
                    )
                )

            wav.writeframes(
                b"".join(frames)
            )

            position = end

    return output_path


# =========================================================
# ADD MUSIC TO SINGLE VIDEO
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

        duration = video.duration

        create_background_music(
            style,
            duration,
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

def split_story_into_parts(
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

    base_size = (
        len(parts)
        // count
    )

    remainder = (
        len(parts)
        % count
    )

    index = 0

    for i in range(
        count
    ):

        size = base_size

        if i < remainder:
            size += 1

        group = " ".join(
            parts[
                index:index + size
            ]
        )

        if group:
            groups.append(
                group
            )

        index += size

    return groups


# =========================================================
# ACTION DETECTION
# =========================================================

def detect_action(text):

    lower = text.lower()

    if any(
        word in lower
        for word in [
            "fly",
            "flies",
            "flying",
            "اڑ",
            "اڑا",
            "اڑتا",
            "اڑنے",
            "उड़",
            "उड़ा",
            "उड़ता"
        ]
    ):

        return (
            "The character flies through the environment, "
            "moves wings naturally, looks around while flying, "
            "then gently changes direction."
        )

    if any(
        word in lower
        for word in [
            "stone",
            "stones",
            "پتھر",
            "पत्थर"
        ]
    ):

        return (
            "The character notices small stones, "
            "moves toward them, picks them up naturally, "
            "and interacts with them carefully."
        )

    if any(
        word in lower
        for word in [
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
        word in lower
        for word in [
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
        word in lower
        for word in [
            "run",
            "runs",
            "running",
            "دوڑ",
            "دوڑتا",
            "दौड़",
            "दौड़ता"
        ]
    ):

        return (
            "The character runs naturally through "
            "the environment with believable body "
            "and leg movement."
        )

    if any(
        word in lower
        for word in [
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
            "looks around, and interacts with "
            "the environment."
        )

    if any(
        word in lower
        for word in [
            "look",
            "looks",
            "see",
            "sees",
            "دیکھ",
            "دیکھتا",
            "देख",
            "देखता"
        ]
    ):

        return (
            "The character slowly looks around, "
            "notices the important object, and "
            "reacts with clear facial expression."
        )

    if any(
        word in lower
        for word in [
            "happy",
            "happily",
            "خوش",
            "خوشی",
            "खुश",
            "खुशी"
        ]
    ):

        return (
            "The character becomes happy, "
            "smiles, moves naturally, and shows "
            "joyful body language."
        )

    if any(
        word in lower
        for word in [
            "sad",
            "sadly",
            "اداس",
            "उदास"
        ]
    ):

        return (
            "The character shows gentle sadness "
            "with natural facial expression and "
            "slow body movement."
        )

    return (
        "Characters perform the action described "
        "in the story naturally; walking, stopping, "
        "looking, turning, interacting with objects, "
        "and using expressive body language when appropriate."
    )


# =========================================================
# CHARACTER DESCRIPTION
# =========================================================

def create_character_description(
    story
):

    lower = story.lower()

    if any(
        word in lower
        for word in [
            "crow",
            "کوا",
            "कौआ"
        ]
    ):

        return (
            "a cute black crow with expressive eyes, "
            "soft cartoon feathers, friendly child-safe design, "
            "consistent appearance"
        )

    if any(
        word in lower
        for word in [
            "rabbit",
            "خرگوش",
            "खरगोश"
        ]
    ):

        return (
            "a cute fluffy rabbit with expressive eyes, "
            "friendly child-safe cartoon design, "
            "consistent appearance"
        )

    if any(
        word in lower
        for word in [
            "fox",
            "لومڑی",
            "लोमड़ी"
        ]
    ):

        return (
            "a friendly orange fox with expressive eyes, "
            "child-safe cartoon design, "
            "consistent appearance"
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

    parts = split_story_into_parts(
        story,
        count
    )

    character_description = (
        create_character_description(
            story
        )
    )

    scenes = []

    for i, part in enumerate(
        parts,
        start=1
    ):

        action = detect_action(
            part
        )

        if language == "اردو":

            story_text = (
                f"{part} — منظر {i}"
            )

            character = (
                character_description
            )

        else:

            story_text = (
                f"{part} — Scene {i}"
            )

            character = (
                character_description
            )

        image_prompt = (
            "2D colorful children's cartoon, "
            "beautiful cinematic environment, "
            "friendly expressive characters, "
            "consistent character design, "
            "child-safe animation style, "
            f"main character design: "
            f"{character_description}, "
            f"story action: {part}, "
            "clear composition, high quality, "
            "same visual world and character appearance"
        )

        animation_prompt = (
            f"{action} "
            "Keep the main character's appearance consistent. "
            "Use natural movement and a gentle cinematic camera."
        )

        scenes.append({
            "scene": i,
            "story": story_text,
            "character": character,
            "image_prompt": image_prompt,
            "animation_prompt": animation_prompt
        })

    return scenes


# =========================================================
# COMBINE VIDEO CLIPS
# =========================================================

def combine_video_clips(
    video_paths,
    output_path,
    target_duration=None
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
                )

        if not clips:

            return (
                None,
                0,
                "کوئی video clips نہیں ملیں۔"
            )

        base_duration = sum(
            clip.duration
            for clip in clips
        )

        if (
            target_duration
            and base_duration < target_duration
        ):

            repeats = int(
                math.ceil(
                    target_duration
                    / base_duration
                )
            )

            extended_clips = []

            for _ in range(
                repeats
            ):

                for clip in clips:

                    extended_clips.append(
                        clip
                    )

            final_video = (
                concatenate_videoclips(
                    extended_clips,
                    method="compose"
                )
            )

            final_video = (
                final_video.subclipped(
                    0,
                    min(
                
