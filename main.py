import os
import json
from pathlib import Path

import streamlit as st

try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None


# ============================================================
# PROJECT SETTINGS
# ============================================================

APP_DIR = Path("cartoon_project")
STATE_FILE = APP_DIR / "story_project.json"

APP_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="AI Cartoon Story Studio",
    page_icon="🎬",
    layout="wide",
)


# ============================================================
# DEFAULT STATE
# ============================================================

def default_state():
    return {
        "story": "",
        "language": "Urdu",
        "cartoon_style": "Original 3D Kids Cartoon",
        "target_audience": "Children",
        "characters": [],
        "locations": [],
        "scenes": [],
    }


def load_state():
    if not STATE_FILE.exists():
        return default_state()

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        state = default_state()
        state.update(data)
        return state

    except Exception:
        return default_state()


def save_state(state):
    with open(
        STATE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )


state = load_state()


# ============================================================
# HF TOKEN
# ============================================================

def get_hf_token():
    try:
        token = st.secrets.get("HF_TOKEN", "")
        if token:
            return token
    except Exception:
        pass

    return os.environ.get("HF_TOKEN", "")


# ============================================================
# AI CLIENT
# ============================================================

def get_ai_client():

    if InferenceClient is None:
        return None, (
            "huggingface_hub installed نہیں ہے۔ "
            "requirements.txt میں اسے شامل کریں۔"
        )

    token = get_hf_token()

    if not token:
        return None, (
            "HF_TOKEN موجود نہیں ہے۔ "
            "اپنے Streamlit Secrets میں HF_TOKEN شامل کریں۔"
        )

    try:
        client = InferenceClient(
            provider="auto",
            api_key=token,
        )

        return client, None

    except Exception as exc:
        return None, str(exc)


# ============================================================
# AI MODEL
# ============================================================

TEXT_MODEL = (
    "meta-llama/Llama-3.1-8B-Instruct"
)


# ============================================================
# JSON CLEANER
# ============================================================

def extract_json(text):

    text = text.strip()

    # Markdown code block remove کریں
    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # پورا JSON object تلاش کریں
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "AI نے valid JSON واپس نہیں کیا۔"
        )

    json_text = text[start:end + 1]

    return json.loads(json_text)


# ============================================================
# STORY PLANNER
# ============================================================

def build_story_prompt(
    story,
    language,
    cartoon_style,
    target_audience,
):

    return f"""
You are a professional children's animation story planner.

Convert the user's story into a production-ready cartoon plan.

IMPORTANT RULES:

1. Preserve the original story meaning.
2. Do not invent unnecessary characters.
3. Keep character appearance consistent.
4. Create a reusable character bible.
5. Create a reusable location bible.
6. Divide the story into logical cinematic scenes.
7. Every scene must contain:
   - visual description
   - action
   - dialogue
   - camera
   - lighting
   - duration
   - image generation prompt
   - animation prompt
8. Make every image prompt describe the same character
   using the character's fixed appearance.
9. Do not copy copyrighted cartoon characters.
10. Create an original visual identity.
11. Keep the story family friendly.
12. Dialogue must be suitable for children.
13. The final output must be valid JSON only.
14. Do not write explanations outside JSON.

LANGUAGE:
{language}

CARTOON STYLE:
{cartoon_style}

TARGET AUDIENCE:
{target_audience}

USER STORY:
{story}

Return exactly this JSON structure:

{{
  "title": "string",
  "logline": "string",

  "visual_style": {{
    "style_name": "string",
    "description": "string",
    "color_direction": "string",
    "lighting_direction": "string",
    "rendering": "string"
  }},

  "characters": [
    {{
      "id": "character_01",
      "name": "string",
      "role": "main/supporting",
      "age_description": "string",
      "species": "string",
      "appearance": "string",
      "clothing": "string",
      "colors": "string",
      "personality": "string",
      "voice_description": "string",
      "character_prompt": "string"
    }}
  ],

  "locations": [
    {{
      "id": "location_01",
      "name": "string",
      "description": "string",
      "environment": "string",
      "colors": "string",
      "lighting": "string",
      "location_prompt": "string"
    }}
  ],

  "scenes": [
    {{
      "id": 1,
      "title": "string",
      "duration_seconds": 6,
      "location_id": "location_01",
      "character_ids": [
        "character_01"
      ],
      "story_summary": "string",
      "action": "string",
      "dialogue": [
        {{
          "character_id": "character_01",
          "text": "string"
        }}
      ],
      "camera": "string",
      "lighting": "string",
      "sound_effects": [
        "string"
      ],
      "music_mood": "string",
      "image_prompt": "string",
      "animation_prompt": "string",
      "negative_prompt": "string"
    }}
  ]
}}
"""


# ============================================================
# GENERATE STORY PLAN
# ============================================================

def generate_story_plan(
    story,
    language,
    cartoon_style,
    target_audience,
):

    client, error = get_ai_client()

    if error:
        return None, error

    prompt = build_story_prompt(
        story=story,
        language=language,
        cartoon_style=cartoon_style,
        target_audience=target_audience,
    )

    try:

        response = client.chat_completion(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional "
                        "children's animation planner. "
                        "Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=8000,
            temperature=0.4,
        )

        content = response.choices[0].message.content

        data = extract_json(content)

        # بنیادی validation
        required = [
            "title",
            "logline",
            "visual_style",
            "characters",
            "locations",
            "scenes",
        ]

        for key in required:
            if key not in data:
                raise ValueError(
                    f"AI output میں '{key}' موجود نہیں۔"
                )

        if not isinstance(
            data["characters"],
            list,
        ):
            raise ValueError(
                "characters list نہیں ہے۔"
            )

        if not isinstance(
            data["locations"],
            list,
        ):
            raise ValueError(
                "locations list نہیں ہے۔"
            )

        if not isinstance(
            data["scenes"],
            list,
        ):
            raise ValueError(
                "scenes list نہیں ہے۔"
            )

        return data, None

    except Exception as exc:

        return None, str(exc)


# ============================================================
# UI
# ============================================================

st.title("🎬 AI Cartoon Story Studio")

st.caption(
    "صرف Script لکھیں → Characters → Scenes → "
    "Image Prompts → Animation Prompts"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Project Settings")

    language = st.selectbox(
        "کہانی کی زبان",
        [
            "Urdu",
            "English",
            "Hindi",
            "Roman Urdu",
        ],
        index=(
            [
                "Urdu",
                "English",
                "Hindi",
                "Roman Urdu",
            ].index(
                state.get(
                    "language",
                    "Urdu",
                )
            )
        ),
    )

    cartoon_style = st.selectbox(
        "Cartoon Style",
        [
            "Original 3D Kids Cartoon",
            "Cute 3D Preschool Cartoon",
            "Colorful 3D Adventure Cartoon",
            "Soft Storybook 3D Cartoon",
            "Funny 3D Family Cartoon",
        ],
        index=(
            [
                "Original 3D Kids Cartoon",
                "Cute 3D Preschool Cartoon",
                "Colorful 3D Adventure Cartoon",
                "Soft Storybook 3D Cartoon",
                "Funny 3D Family Cartoon",
            ].index(
                state.get(
                    "cartoon_style",
                    "Original 3D Kids Cartoon",
                )
            )
        ),
    )

    target_audience = st.selectbox(
        "Audience",
        [
            "Children",
            "Family",
            "Preschool",
        ],
        index=(
            [
                "Children",
                "Family",
                "Preschool",
            ].index(
                state.get(
                    "target_audience",
                    "Children",
                )
            )
        ),
    )


# ============================================================
# STORY INPUT
# ============================================================

st.subheader("📝 اپنی مکمل کہانی لکھیں")

story = st.text_area(
    "Story",
    value=state.get("story", ""),
    height=300,
    placeholder=(
        "مثال:\n\n"
        "ایک چھوٹا سا خرگوش جنگل میں رہتا تھا۔ "
        "ایک دن اسے ایک زخمی پرندہ ملا..."
    ),
)


# ============================================================
# GENERATE BUTTON
# ============================================================

if st.button(
    "🚀 Script کو Cartoon Plan میں تبدیل کریں",
    type="primary",
    use_container_width=True,
):

    if not story.strip():

        st.warning(
            "پہلے اپنی مکمل کہانی لکھیں۔"
        )

    else:

        with st.spinner(
            "AI آپ کی کہانی کو cartoon production plan میں تبدیل کر رہا ہے..."
        ):

            result, error = generate_story_plan(
                story=story.strip(),
                language=language,
                cartoon_style=cartoon_style,
                target_audience=target_audience,
            )

        if error:

            st.error(
                "Generation میں مسئلہ آیا:"
            )

            st.code(error)

        else:

            state["story"] = story.strip()
            state["language"] = language
            state["cartoon_style"] = cartoon_style
            state["target_audience"] = target_audience

            state["characters"] = result[
                "characters"
            ]

            state["locations"] = result[
                "locations"
            ]

            state["scenes"] = result[
                "scenes"
            ]

            save_state(state)

            st.success(
                "🎉 Cartoon production plan تیار ہے!"
            )


# ============================================================
# DISPLAY RESULT
# ============================================================

if state["characters"]:

    st.divider()

    st.header("👨‍👩‍👧 Characters")

    for character in state["characters"]:

        with st.expander(
            f"{character.get('name', 'Character')} "
            f"— {character.get('role', '')}"
        ):

            st.write(
                "**Appearance:**",
                character.get(
                    "appearance",
                    "",
                ),
            )

            st.write(
                "**Clothing:**",
                character.get(
                    "clothing",
                    "",
                ),
            )

            st.write(
                "**Personality:**",
                character.get(
                    "personality",
                    "",
                ),
            )

            st.write(
                "**Voice:**",
                character.get(
                    "voice_description",
                    "",
                ),
            )

            st.write(
                "**Character Generation Prompt:**"
            )

            st.code(
                character.get(
                    "character_prompt",
                    "",
                ),
                language="text",
            )


# ============================================================
# LOCATIONS
# ============================================================

if state["locations"]:

    st.divider()

    st.header("🌳 Locations")

    for location in state["locations"]:

        with st.expander(
            location.get(
                "name",
                "Location",
            )
        ):

            st.write(
                location.get(
                    "description",
                    "",
                )
            )

            st.write(
                "**Environment:**",
                location.get(
                    "environment",
                    "",
                ),
            )

            st.write(
                "**Location Prompt:**"
            )

            st.code(
                location.get(
                    "location_prompt",
                    "",
                ),
                language="text",
            )


# ============================================================
# SCENES
# ============================================================

if state["scenes"]:

    st.divider()

    st.header("🎬 Scenes")

    for scene in state["scenes"]:

        with st.expander(
            f"Scene {scene.get('id')} — "
            f"{scene.get('title', '')}"
        ):

            st.write(
                "**Duration:**",
                scene.get(
                    "duration_seconds",
                    6,
                ),
                "seconds",
            )

            st.write(
                "**Story:**",
                scene.get(
                    "story_summary",
                    "",
                ),
            )

            st.write(
                "**Action:**",
                scene.get(
                    "action",
                    "",
                ),
            )

            st.write(
                "**Camera:**",
                scene.get(
                    "camera",
                    "",
                ),
            )

            st.write(
                "**Lighting:**",
                scene.get(
                    "lighting",
                    "",
                ),
            )

            st.write(
                "**Music:**",
                scene.get(
                    "music_mood",
                    "",
                ),
            )

            # Dialogue
            st.subheader("🗣️ Dialogue")

            dialogue = scene.get(
                "dialogue",
                [],
            )

            if dialogue:

                for line in dialogue:

                    st.write(
                        f"**{line.get('character_id', '')}:** "
                        f"{line.get('text', '')}"
                    )

            else:

                st.write(
                    "اس scene میں dialogue نہیں ہے۔"
                )

            # SFX
            st.subheader("🔊 Sound Effects")

            sfx = scene.get(
                "sound_effects",
                [],
            )

            if sfx:

                for sound in sfx:
                    st.write(
                        f"• {sound}"
                    )

            # IMAGE PROMPT
            st.subheader(
                "🎨 Image Generation Prompt"
            )

            st.code(
                scene.get(
                    "image_prompt",
                    "",
                ),
                language="text",
            )

            # ANIMATION PROMPT
            st.subheader(
                "🎬 Animation Generation Prompt"
            )

            st.code(
                scene.get(
                    "animation_prompt",
                    "",
                ),
                language="text",
            )

            # NEGATIVE PROMPT
            st.subheader(
                "🚫 Negative Prompt"
            )

            st.code(
                scene.get(
                    "negative_prompt",
                    "",
                ),
                language="text",
            )


# ============================================================
# DOWNLOAD JSON
# ============================================================

if state["scenes"]:

    st.divider()

    project_json = json.dumps(
        state,
        ensure_ascii=False,
        indent=2,
    )

    st.download_button(
        "⬇️ Cartoon Production JSON Download کریں",
        data=project_json,
        file_name="cartoon_project.json",
        mime="application/json",
        use_container_width=True,
)
