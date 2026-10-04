import streamlit as st

st.set_page_config(
    page_title="My AI Cartoon Videos",
    page_icon="🎬"
)

st.title("🎬 My AI Cartoon Videos")
st.write("اپنے کردار کے نام سے مکمل Cartoon Script بنائیں")

character = st.text_input(
    "اپنے کردار کا نام لکھیں:",
    placeholder="مثلاً: آلو، کتا، شیر"
)

story_idea = st.text_area(
    "کہانی کا خیال لکھیں:",
    placeholder="مثلاً: اپنے دوست کے ساتھ ایک دلچسپ سفر"
)

if st.button("✨ مکمل کہانی بنائیں", type="primary"):

    if not character.strip():
        st.warning("پہلے کردار کا نام لکھیں۔")

    elif not story_idea.strip():
        st.warning("پہلے کہانی کا خیال لکھیں۔")

    else:

        scenes = [
            f"{character} ایک خوبصورت صبح اٹھتا ہے۔",
            f"{character} کو ایک دلچسپ مسئلہ نظر آتا ہے۔",
            f"{character} اس مسئلے کا حل تلاش کرنے نکلتا ہے۔",
            f"راستے میں {character} اپنے ایک دوست سے ملتا ہے۔",
            f"{character} اور اس کا دوست مل کر ایک منصوبہ بناتے ہیں۔",
            f"ان کا پہلا منصوبہ ناکام ہو جاتا ہے، لیکن {character} ہمت نہیں ہارتا۔",
            f"{character} دوبارہ کوشش کرتا ہے اور ایک نیا راستہ تلاش کرتا ہے۔",
            f"{character} آخرکار مسئلے کا حل تلاش کر لیتا ہے۔",
            f"{character} اور اس کے دوست بہت خوش ہوتے ہیں۔",
            f"{character} سیکھتا ہے کہ ہمت اور کوشش کبھی ضائع نہیں جاتی۔"
        ]

        st.success(f"🎬 {character} کی مکمل کہانی تیار ہے!")

        for i, scene in enumerate(scenes, 1):
            st.subheader(f"Scene {i}")
            st.write(scene)

        st.divider()

        st.subheader("📜 مکمل اسکرپٹ")

        full_script = "\n\n".join(
            [f"Scene {i}: {scene}" for i, scene in enumerate(scenes, 1)]
        )

        st.write(full_script)
