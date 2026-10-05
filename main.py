
import os
import json
import re
from pathlib import Path

import streamlit as st
from huggingface_hub import InferenceClient


# =========================================================
# SETTINGS
# =========================================================

APP_DIR = Path("cartoon_project")
IMAGE_DIR = APP_DIR / "images"
VIDEO_DIR = APP_DIR / "videos"

APP_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)

PROJECT_FILE = APP_DIR / "project.json"


IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"

# Video model کو ابھی خالی رکھیں۔
# بعد میں Hugging Face پر available image-to-video model
# یہاں set کیا جا سکتا ہے۔
VIDEO_MODEL = ""


# =========================================================
# SECRETS
# =========================================================

def get_hf_token():
    try:
        token = st.secrets.get("HF_TOKEN")
        if token:
            return token
    except Exception:
        pass

    return os.getenv("HF_TOKEN", "")


# =========================================================
# PROJECT
# =========================================================

def empty_project():
    return {
        "title": "",
        "language": "Urdu",
        "style": (
            "original preschool 3D cartoon, "
            "colorful rounded characters, "
            "friendly expressive faces, "
            "soft cinematic lighting"
        ),
        "story": "",
        "characters": [],
        "locations": [],
        "scenes": [],
        "images": [],
        "videos": []
    }


def load_project():
    if PROJECT_FILE.exists():
        try:
            return json.loads(
                PROJECT_FILE.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            pass

    return empty_project()


def save_project(project):
    PROJECT_FILE.write_text(
        json.dumps(
            project,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# =========================================================
# JSON HELPER
# =========================================================

def extract_json(text):

    text = text.strip()

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace(
        "```",
        ""
    ).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "AI نے valid JSON واپس نہیں کیا۔"
        )

    return json.loads(
        text[start:end + 1]
    )


# =========================================================
# AI STORY PLANNER
# =========================================================

def create_story_plan(
    story,
    language,
    style
):

    token = get_hf_token()

    if not token:
        raise RuntimeError(
            "HF_TOKEN Streamlit Secrets میں موجود نہیں ہے۔"
        )

    client = InferenceClient(
        api_key=token,
        provider="auto"
    )

    system_prompt = """
You are an expert children's animated movie planner.

Convert the user's story into a production-ready
cartoon movie plan.

The visual style must be ORIGINAL.
Do not copy Cocomelon or any existing copyrighted
cartoon exactly.

Return ONLY valid JSON.

Required JSON:

{
  "title": "...",

  "characters": [
    {
      "id": "character_1",
      "name": "...",
      "role": "...",
      "species": "...",
      "appearance": "...",
      "clothing": "...",
      "colors": "...",
      "personality": "...",
      "character_prompt": "..."
    }
  ],

  "locations": [
    {
      "id": "location_1",
      "name": "...",
      "description": "...",
      "location_prompt": "..."
    }
  ],

  "scenes": [
    {
      "id": "scene_1",
      "title": "...",
      "duration_seconds": 5,
      "location_id": "location_1",
      "character_ids": ["character_1"],
      "story_summary": "...",
      "action": "...",
      "dialogue": [
        {
          "character_id": "character_1",
          "text": "..."
        }
      ],
      "camera": "...",
      "lighting": "...",
      "image_prompt": "...",
      "animation_prompt": "...",
      "negative_prompt": "...",
      "music_mood": "happy"
    }
  ]
}

Rules:

- Keep characters visually consistent.
- Keep clothing and colors consistent.
- Every scene must use existing character IDs.
- Every scene must use an existing location ID.
- Scene duration should normally be 4-8 seconds.
- Dialogue should be short.
- Image prompts must be detailed.
- Animation prompts must describe movement.
- Make the movie suitable for children.
"""

    user_prompt = f"""
Language:
{language}

Visual Style:
{style}

Story:
{story}
"""

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        max_tokens=7000,
        temperature=0.3
    )

    text = response.choices[0].message.content

    return extract_json(text)


# =========================================================
# CHARACTER CONTEXT
# =========================================================

def get_character_context(
    project,
    character_ids
):

    output = []

    characters = {
        c.get("id"): c
        for c in project.get(
            "characters",
            []
        )
    }

    for cid in character_ids:

        character = characters.get(cid)

        if not character:
            continue

        output.append(
            f"""
Character:
Name: {character.get("name", "")}
Species: {character.get("species", "")}
Appearance: {character.get("appearance", "")}
Clothing: {character.get("clothing", "")}
Colors: {character.get("colors", "")}
Personality: {character.get("personality", "")}
"""
        )

    return "\n".join(output)


# =========================================================
# LOCATION CONTEXT
# =========================================================

def get_location_context(
    project,
    location_id
):

    for location in project.get(
        "locations",
        []
    ):

        if location.get("id") == location_id:

            return f"""
Location:
{location.get("name", "")}

Description:
{location.get("description", "")}
"""

    return ""


# =========================================================
# FINAL IMAGE PROMPT
# =========================================================

def make_image_prompt(
    project,
    scene
):

    characters = get_character_context(
        project,
        scene.get(
            "character_ids",
            []
        )
    )

    location = get_location_context(
        project,
        scene.get(
            "location_id",
            ""
        )
    )

    style = project.get(
        "style",
        "original preschool 3D cartoon"
    )

    return f"""
{style}

CHARACTER DESIGN:
{characters}

LOCATION:
{location}

SCENE:
{scene.get("story_summary", "")}

ACTION:
{scene.get("action", "")}

CAMERA:
{scene.get("camera", "")}

LIGHTING:
{scene.get("lighting", "")}

ORIGINAL IMAGE DESCRIPTION:
{scene.get("image_prompt", "")}

Create a high-quality 16:9 children's
3D animation movie frame.

Keep all characters consistent.

Same face.
Same body proportions.
Same clothes.
Same colors.

Friendly expressive faces.
Beautiful colorful environment.
Soft cinematic lighting.
Clean composition.
Detailed 3D cartoon rendering.

No text.
No subtitles.
No logo.
No watermark.
"""


# =========================================================
# IMAGE GENERATION
# =========================================================

def generate_image(
    prompt,
    filename
):

    token = get_hf_token()

    if not token:
        raise RuntimeError(
            "HF_TOKEN موجود نہیں ہے۔"
        )

    client = InferenceClient(
        api_key=token,
        provider="auto"
    )

    image = client.text_to_image(
        prompt=prompt,
        model=IMAGE_MODEL,
        width=1280,
        height=720,
        num_inference_steps=4
    )

    path = IMAGE_DIR / filename

    image.save(path)

    return str(path)


# =========================================================
# IMAGE → VIDEO
# =========================================================

def generate_video(
    image_path,
    prompt,
    filename,
    negative_prompt=""
):

    token = get_hf_token()

    if not token:
        raise RuntimeError(
            "HF_TOKEN موجود نہیں ہے۔"
        )

    if not VIDEO_MODEL:
        raise RuntimeError(
            """
VIDEO_MODEL ابھی configure نہیں ہے۔

پہلے Image generation test کریں۔
Video model بعد میں configure ہوگا۔
"""
        )

    client = InferenceClient(
        api_key=token,
        provider="auto"
    )

    video_bytes = client.image_to_video(
        image=image_path,
        model=VIDEO_MODEL,
        prompt=prompt,
        negative_prompt=negative_prompt
    )

    output = VIDEO_DIR / filename

    output.write_bytes(
        video_bytes
    )

    return str(output)


# =========================================================
# GENERATE ALL IMAGES
# =========================================================

def generate_all_images(project):

    scenes = project.get(
        "scenes",
        []
    )

    if not scenes:
        raise RuntimeError(
            "پہلے Story Plan بنائیں۔"
        )

    results = []

    progress = st.progress(0)

    for index, scene in enumerate(
        scenes
    ):

        scene_number = index + 1

        st.write(
            f"🎨 Scene {scene_number}/{len(scenes)} image..."
        )

        prompt = make_image_prompt(
            project,
            scene
        )

        filename = (
            f"scene_{scene_number:03d}.png"
        )

        image_path = generate_image(
            prompt,
            filename
        )

        results.append(
            image_path
        )

        progress.progress(
            scene_number / len(scenes)
        )

    project["images"] = results

    save_project(project)

    return project


# =========================================================
# STREAMLIT
# =========================================================

st.set_page_config(
    page_title="AI Cartoon Movie",
    page_icon="🎬",
    layout="wide"
)

st.title(
    "🎬 AI Cartoon Movie Generator"
)

st.caption(
    "Script → Story → Characters → Scenes → Images → Video"
)

project = load_project()


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "📝 Script",
        "🎨 Images",
        "🎬 Video"
    ]
)


# =========================================================
# SCRIPT TAB
# =========================================================

with tab1:

    st.header(
        "اپنی کہانی لکھیں"
    )

    language = st.selectbox(
        "Language",
        [
            "Urdu",
            "Hindi",
            "English"
        ]
    )

    style = st.text_input(
        "Cartoon Style",
        value=project.get(
            "style",
            "original preschool 3D cartoon"
        )
    )

    story = st.text_area(
        "Story / Script",
        value=project.get(
            "story",
            ""
        ),
        height=300
    )

    if st.button(
        "🧠 Story کو Cartoon Plan بنائیں",
        type="primary",
        use_container_width=True
    ):

        if not story.strip():

            st.error(
                "پہلے story لکھیں۔"
            )

        else:

            with st.spinner(
                "AI story کو scenes میں تبدیل کر رہا ہے..."
            ):

                try:

                    plan = create_story_plan(
                        story,
                        language,
                        style
                    )

                    project.update(plan)

                    project["story"] = story
                    project["language"] = language
                    project["style"] = style

                    save_project(project)

                    st.success(
                        "Cartoon Plan تیار ہوگیا۔"
                    )

                except Exception as error:

                    st.error(
                        str(error)
                    )


    if project.get("characters"):

        st.subheader(
            "👧 Characters"
        )

        for character in project[
            "characters"
        ]:

            st.write(
                f"**{character.get('name')}** — "
                f"{character.get('appearance')}"
            )


    if project.get("scenes"):

        st.subheader(
            "🎞 Scenes"
        )

        for scene in project[
            "scenes"
        ]:

            with st.expander(
                f"{scene.get('id')} — "
                f"{scene.get('title')}"
            ):

                st.write(
                    scene
                )


# =========================================================
# IMAGE TAB
# =========================================================

with tab2:

    st.header(
        "🎨 Scene Images"
    )

    if not project.get("scenes"):

        st.info(
            "پہلے Script tab میں Cartoon Plan بنائیں۔"
        )

    else:

        if st.button(
            "🎨 تمام Scene Images بنائیں",
            type="primary",
            use_container_width=True
        ):

            try:

                project = generate_all_images(
                    project
                )

                st.success(
                    "تمام images تیار ہوگئی ہیں۔"
                )

            except Exception as error:

                st.error(
                    str(error)
                )


        for image in project.get(
            "images",
            []
        ):

            if Path(image).exists():

                st.image(
                    image,
                    use_container_width=True
                )


# =========================================================
# VIDEO TAB
# =========================================================

with tab3:

    st.header(
        "🎬 Image → Video"
    )

    st.info(
        """
Image generation یہاں مکمل کی گئی ہے۔

Video generation کے لیے پہلے مناسب
Hugging Face image-to-video model configure کرنا ہوگا۔
"""
    )

    if not project.get("images"):

        st.warning(
            "پہلے Images بنائیں۔"
        )

    else:

        if not VIDEO_MODEL:

            st.warning(
                "VIDEO_MODEL ابھی configure نہیں ہے۔"
            )

        else:

            if st.button(
                "🎬 تمام Images کو Videos میں تبدیل کریں",
                type="primary",
                use_container_width=True
            ):

                videos = []

                for index, scene in enumerate(
                    project.get("scenes", [])
                ):

                    image_path = project[
                        "images"
                    ][index]

                    prompt = scene.get(
                        "animation_prompt",
                        scene.get(
                            "action",
                            "gentle natural movement"
                        )
                    )

                    negative = scene.get(
                        "negative_prompt",
                        "blurry, distorted, text, watermark"
                    )

                    try:

                        video = generate_video(
                            image_path,
                            prompt,
                            f"scene_{index + 1:03d}.mp4",
                            negative
                        )

                        videos.append(
                            video
                        )

                        st.video(
                            video
                        )

                    except Exception as error:

                        st.error(
                            f"Scene {index + 1}: {error}"
                        )

                project["videos"] = videos

                save_project(
                    project
        )
