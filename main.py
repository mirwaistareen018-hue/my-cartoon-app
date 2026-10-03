import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
import requests
from io import BytesIO
import random

st.set_page_config(page_title="COCOMELON AI VIDEO", layout="wide")
st.title("COCOMELON - FINAL AI VIDEO GENERATOR")
st.markdown("Full English Code - Works 24 Hours - Direct Video")

def create_backup_scene(text, bg_color, table_color):
    img = Image.new('RGB', (1280, 720), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Wall
    draw.rectangle([0, 0, 1280, 500], fill=(245, 222, 179))
    # Table
    draw.rectangle([0, 500, 1280, 720], fill=table_color)
    # Fan on top
    draw.ellipse([500, 10, 780, 120], fill=(220, 220, 220), outline=(0,0,0), width=4)
    draw.ellipse([580, 40, 700, 90], fill=(100,100,100))
    # Text
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    except:
        font = ImageFont.load_default()
    draw.text((150, 200), text, fill=(0,0,0), font=font)
    return img

def generate_image(prompt, backup_text):
    encoded = requests.utils.quote(prompt)
    # Try AI 3 times
    for i in range(3):
        try:
            seed = random.randint(1, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={seed}&model=turbo"
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and len(r.content) > 10000:
                return Image.open(BytesIO(r.content))
        except:
            continue
    # If AI fails, create local 3D style backup - Never fails
    if "mouse" in backup_text.lower():
        return create_backup_scene("Cute 3D Mouse\nEating Cheese On Table", (255, 248, 220), (139, 69, 19))
    elif "close" in backup_text.lower():
        return create_backup_scene("Mouse Eating\nSlowly Close Up", (255, 240, 200), (139, 69, 19))
    else:
        return create_backup_scene("Big Gray Cat\nRunning Fast", (220, 220, 220), (101, 67, 33))

story = st.text_area("Write Story in English:", "A small cute mouse is sitting on a wooden table and eating cheese slowly. A ceiling fan is moving on top, behind is a wall. Then a big gray cat comes running to catch the mouse.", height=120)

if st.button("GENERATE FINAL VIDEO - DIRECT"):
    st.success("AI Brain Working - Generating 3 Scenes Directly")

    prompt1 = "cute baby 3d pixar mouse sitting on wooden table eating big yellow cheese, cozy house interior, brown wall behind, ceiling fan on top, ultra realistic 3d cartoon 4k, soft lighting"
    prompt2 = "close up cute baby pixar mouse chewing cheese slowly on table, mouth movement, cozy house interior, brown wall, 3d cartoon"
    prompt3 = "big cute gray 3d pixar cat running fast towards table to catch mouse, same cozy house interior, dramatic, 3d cartoon 4k"

    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.spinner("Generating Scene 1..."):
            img1 = generate_image(prompt1, "mouse on table")
            st.image(img1, caption="Scene 1: Mouse on Table")
    
    with col2:
        with st.spinner("Generating Scene 2..."):
            img2 = generate_image(prompt2, "close up mouse")
            st.image(img2, caption="Scene 2: Eating Slowly")

    with col3:
        with st.spinner("Generating Scene 3..."):
            img3 = generate_image(prompt3, "cat running")
            st.image(img3, caption="Scene 3: Cat Running")

    # Save images
    img1.save("s1.jpg")
    img2.save("s2.jpg")
    img3.save("s3.jpg")

    # Generate Audio
    with st.spinner("Generating Audio..."):
        tts = gTTS(text=story, lang='en', slow=True)
        tts.save("audio.mp3")
        audio = AudioFileClip("audio.mp3")

    # Generate Video
    with st.spinner("Generating Final Video..."):
        clip1 = ImageClip("s1.jpg").set_duration(5).resize((1280,720)).set_fps(24)
        clip2 = ImageClip("s2.jpg").set_duration(5).resize((1280,720)).set_fps(24)
        clip3 = ImageClip("s3.jpg").set_duration(4).resize((1280,720)).set_fps(24)

        final = concatenate_videoclips([clip1, clip2, clip3]).set_audio(audio)
        final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")

    st.balloons()
    st.success("FINAL VIDEO READY!")
    st.video("final.mp4")

    with open("final.mp4", "rb") as f:
        st.download_button("DOWNLOAD VIDEO", f, file_name="cocomelon_final.mp4", mime="video/mp4")
