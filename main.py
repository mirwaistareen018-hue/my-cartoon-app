import streamlit as st
import os
import re
import math

st.set_page_config(
    page_title="AI Cartoon Movie Generator",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 AI Cartoon Movie Generator")
st.caption("AI Cartoon Movie Project — Safe Starter Version")

story = st.text_area(
    "📝 اپنی Full Story / Script یہاں لکھیں",
    height=220,
    placeholder="مثال: ایک پیاسا کوا جنگل میں اڑ رہا تھا...",
)

duration = st.selectbox(
    "⏱️ Movie Duration",
    [2, 3, 4, 5],
    index=0,
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

clips_per_scene = st.selectbox(
    "🎥 Clips per Scene",
    [1, 2, 3],
    index=0,
)


def split_story(text, count):
    parts = re.split(
        r"(?<=[.!?۔])\s+|\n+",
        text.strip(),
    )

    parts = [
        p.strip()
        for p in parts
        if p.strip()
    ]

    if not parts:
        return []

    if len(parts) <= count:
        return parts

    size = math.ceil(len(parts) / count)

    return [
        " ".join(parts[i:i + size])
        for i in range(0, len(parts), size)
    ][:count]


if st.button(
    "🧠 Create Cartoon Movie Project",
    use_container_width=True,
    type="primary",
):
    if not story.strip():
        st.warning("پہلے story لکھیں۔")
    else:
        scenes = split_story(
            story,
            duration * 4,
        )

        st.session_state["scenes"] = scenes

        st.success(
            f"✅ {len(scenes)} scenes تیار ہیں۔"
        )


if (
    "scenes" in st.session_state
    and st.session_state["scenes"]
):
    st.divider()

    st.header("🎭 Scene Plan")

    for i, scene in enumerate(
        st.session_state["scenes"],
        1,
    ):
        with st.container(border=True):
            st.subheader(
                f"Scene {i}"
            )

            st.write(scene)

            st.caption(
                "🎬 AI motion: scene کے مطابق "
                "natural movement تیار کیا جائے گا۔"
            )

    st.divider()

    st.info(
        "✅ بنیادی app screen بحال ہے۔ "
        "اگلے مرحلے میں اسی محفوظ base کے اوپر "
        "AI image, AI motion, music, narrator "
        "اور final movie engine شامل کیے جائیں گے۔"
    )


st.sidebar.header("⚙️ Project Status")
st.sidebar.write("App: Running")
st.sidebar.write("UI: Safe Mode")
st.sidebar.write("Movie Engine: Ready for next stage")
