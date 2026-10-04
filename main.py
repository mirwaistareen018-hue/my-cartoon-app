import streamlit as st

st.set_page_config(
    page_title="My AI Cartoon Videos",
    page_icon="🎬"
)

st.title("🎬 My AI Cartoon Videos")
st.write("مفت Cartoon Story Generator")

story_idea = st.text_area(
    "اپنی کہانی کا خیال لکھیں:",
    placeholder="مثلاً: ایک پیاسا کوا پانی تلاش کرتا ہے"
)

story_length = st.selectbox(
    "کہانی کی لمبائی:",
    ["Short", "Medium", "Long"]
)

if st.button("✨ کہانی بنائیں", type="primary"):

    if not story_idea.strip():
        st.warning("پہلے کہانی کا خیال لکھیں۔")

    else:
        scenes = {
            "Short": 5,
            "Medium": 10,
            "Long": 20
        }

        total_scenes = scenes[story_length]

        st.success(f"کہانی تیار ہے — {total_scenes} Scenes")

        for i in range(1, total_scenes + 1):
            st.write(
                f"### Scene {i}\n"
                f"{story_idea} — اس Scene میں کہانی کا نیا حصہ شروع ہوتا ہے۔"
            )
