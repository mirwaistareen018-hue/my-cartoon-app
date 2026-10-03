import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
import time

st.set_page_config(page_title="COCOMELON AI BRAIN V4", layout="wide")
st.title("🧠 COCOMELON - MUKAMMAL AI VIDEO 🧠")
st.markdown("Ab AI khud Choha, Cheese aur Video banayega - Ahista Ahista khata hua")

def generate_ai_image(prompt):
    # Free AI Image - 3D Cartoon
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&nologo=true&enhance=true"
    try:
        r = requests.get(url, timeout=45)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content))
    except:
        return None

story = st.text_area("Kahani likho:", "Ek chota choha mez par beth kar cheese ahista ahista kha raha hai, upar pankha chal raha hai, peeche deewar hai. Phir billi ati hai.", height=120)

if st.button("🚀 MUKAMMAL VIDEO GENERATE KARO"):
    st.info("🧠 AI Apne Dimagh Se Soch Raha Hai... Choha, Cheese, Table, Wall, Fan bana raha hai")
    
    p1 = "cute baby 3d pixar mouse sitting on wooden table eating a big yellow cheese slowly, cheese on small plate, cozy house interior, brown wall behind, ceiling fan on top, soft light, ultra cute 3d cartoon"
    
    p2 = "same cute 3d pixar baby mouse eating cheese on table, close up shot, mouth chewing cheese, cozy house interior, brown wall, ceiling fan, 3d cartoon"
    
    p3 = "big cute gray 3d cat entering house and running towards table to catch mouse, same cozy house interior, table with cheese, Pixar style"

    with st.spinner("AI Scene 1 bana raha hai - Choha cheese kha raha hai..."):
        img1 = generate_ai_image(p1)
    with st.spinner("AI Scene 2 bana raha hai - Close up ahista kha raha hai..."):
        img2 = generate_ai_image(p2)
    with st.spinner("AI Scene 3 bana raha hai - Billi aa rahi hai..."):
        img3 = generate_ai_image(p3)

    if img1 and img2 and img3:
        img1.save("s1.jpg"); img2.save("s2.jpg"); img3.save("s3.jpg"
        )
        c1,c2,c3 = st.columns(3)
        c1.image(img1, caption="Scene 1: Table par cheese")
        c2.image(img2, caption="Scene 2: Ahista kha raha hai")
        c3.image(img3, caption="Scene 3: Billi a gai")

        # Voice
        tts = gTTS(text=story, lang='en', slow=True) # slow=True se ahista bolega
        tts.save("audio.mp3")
        audio = AudioFileClip("audio.mp3")

        # Video - Ahista Ahista wala effect
        clip1 = ImageClip("s1.jpg").set_duration(5).resize((1280,720)).set_fps(24)
        clip2 = ImageClip("s2.jpg").set_duration(5).resize((1280,720)).set_fps(24)
        clip3 = ImageClip("s3.jpg").set_duration(4).resize((1280,720)).set_fps(24)

        final = concatenate_videoclips([clip1, clip2, clip3])
        final = final.set_audio(audio)
        final.write_videofile("final.mp4", fps=24, codec="libx264")

        st.success("Mukammal Video Tayyar Hai!")
        st.video("final.mp4")
        with open("final.mp4","rb") as f:
            st.download_button("📥 MUKAMMAL VIDEO DOWNLOAD KARO", f, "choha_cheese_video.mp4")
    else:
        st.error("AI image nahi bani, dobara Generate dabao")
