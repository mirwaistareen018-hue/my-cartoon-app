import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw
import numpy as np
import random
from moviepy.editor import VideoClip, AudioFileClip

st.set_page_config(page_title="Cocomelon A to Z - 10K Models", page_icon="🌈", layout="wide")

st.markdown("<h1 style='text-align:center; color:#FF0000;'>🌈 COCOMELON PRO - A TO Z JUNGLE & 10K MODELS STUDIO 🌈</h1>", unsafe_allow_html=True)

# --- DATABASE - 100% ENGLISH ---
CHARACTERISTICS_DB = {
    "Cat": {"color": (255, 182, 193), "trait": "Cute, Meow Meow, Loves Milk, Funny Dancing"},
    "Dog": {"color": (210, 180, 140), "trait": "Loyal, Bark Bark, Loves Ball, Running Fast"},
    "Cow": {"color": (255, 255, 255), "trait": "Moo Moo, Gives Milk, Calm, White with Black Spots"},
    "Buffalo": {"color": (60, 60, 60), "trait": "Strong, Black, Loves Water, Loud Moo"},
    "Lion": {"color": (255, 215, 0), "trait": "King of Jungle, Roar, Brave, Golden Hair"},
    "Elephant": {"color": (150, 150, 150), "trait": "Big Nose, Large Ears, Slow and Kind"},
    "Monkey": {"color": (139, 69, 19), "trait": "Jumping, Eating Banana, Funny, Climbing Tree"},
    "Rabbit": {"color": (255, 240, 245), "trait": "Small, White, Jumping Fast, Eating Carrot"},
    "Tiger": {"color": (255, 165, 0), "trait": "Striped, Fast Running, Brave"},
    "Zebra": {"color": (240, 240, 240), "trait": "Black and White Stripes, Running in Jungle"},
    "Bear": {"color": (101, 67, 33), "trait": "Brown, Big, Loves Honey"},
    "Giraffe": {"color": (255, 223, 128), "trait": "Long Neck, Tall, Eating Leaves"},
}

JUNGLE_TOOLS = ["Green Jungle", "Farm House", "River Side", "Beach", "Snow Mountain", "Night Jungle", "Village", "School"]

ALL_10K_MODELS = []
for i in range(1, 10001):
    animal = random.choice(list(CHARACTERISTICS_DB.keys()))
    jungle = random.choice(JUNGLE_TOOLS)
    action = random.choice(["Dancing and Singing ABC", "Eating and Playing", "Going to School", "Running and Jumping", "Bathing and Brushing Teeth"])
    ALL_10K_MODELS.append(f"Model {i} - {animal} {action} in {jungle}")

VOICE_IDS = {
    "Ana - Cute Baby Girl (Most Viral)": "en-US-AnaNeural",
    "Ava - Tiny Fairy Girl": "en-US-AvaMultilingualNeural",
    "Jenny - School Girl": "en-US-JennyNeural",
    "Emma - UK Little Girl": "en-GB-LibbyNeural",
}

async def make_child_voice(text, voice_id):
    communicate = edge_tts.Communicate(text, voice_id, pitch="+18Hz", rate="+0%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI - 100% ENGLISH ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Video Tools & Models")
    selected_model = st.selectbox(f"Select Model (10,000+ Models)", ALL_10K_MODELS, index=0)
    bg_tool = st.selectbox("Select Background Tool", JUNGLE_TOOLS)
    prompt = st.text_area("Chat Prompt - Enter Story", "Mimi cat, dog, cow and buffalo are best friends, they go to jungle school and sing ABC song", height=130)

with col2:
    st.subheader("2. Characters Selection")
    selected_animals = st.multiselect("Select Animals (All will be visible)", list(CHARACTERISTICS_DB.keys()), default=["Cat", "Dog", "Cow", "Buffalo", "Lion"])
    voice_choice = st.selectbox("Select Kids Voice", list(VOICE_IDS.keys()))

with col3:
    st.subheader("3. Characteristics")
    if selected_animals:
        for anim in selected_animals:
            trait = CHARACTERISTICS_DB[anim]["trait"]
            st.info(f"**{anim}**: {trait}")

st.divider()

if st.button("🚀 GENERATE FULL A TO Z VIDEO - AUTO", type="primary", use_container_width=True):
    char_details = ", ".join([f"{a} is {CHARACTERISTICS_DB[a]['trait']}" for a in selected_animals])
    full_story = f"Hello kids! Welcome to Cocomelon! {prompt}. Today our heroes are {char_details}. They are in {bg_tool}. This is {selected_model}. They sing Twinkle Twinkle Little Star, Johnny Johnny Yes Papa, Wheels on the bus! ABC song!"

    st.success("Story Generated!")
    st.write(full_story)

    with st.spinner("Generating Kids Voice..."):
        try:
            audio_bytes = asyncio.run(make_child_voice(full_story, VOICE_IDS[voice_choice]))
            with open("voice.mp3", "wb") as f:
                f.write(audio_bytes)
            st.audio(audio_bytes)
        except Exception as e:
            tts = gTTS(full_story, lang='en')
            tts.save("voice.mp3")
            st.audio("voice.mp3")

    with st.spinner("Generating Video - All Characters Visible..."):
        def make_frame(t):
            if "Farm" in bg_tool:
                img = Image.new('RGB', (1280, 720), (135, 206, 235))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(50, 205, 50))
            elif "Beach" in bg_tool:
                img = Image.new('RGB', (1280, 720), (135, 206, 250))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(238, 221, 130))
            elif "Snow" in bg_tool:
                img = Image.new('RGB', (1280, 720), (220, 240, 255))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(255, 255, 255))
            elif "Night" in bg_tool:
                img = Image.new('RGB', (1280, 720), (10, 20, 50))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(20, 50, 20))
                d.ellipse([1000, 50, 1120, 170], fill=(255, 255, 180))
            else:
                img = Image.new('RGB', (1280, 720), (34, 139, 34))
                d = ImageDraw.Draw(img)
                for i in range(7):
                    x = i*180
                    d.rectangle([x+80, 100, x+100, 500], fill=(101, 67, 33))
                    d.ellipse([x+20, 20, x+160, 150], fill=(0, 100, 0))
                d.rectangle([0, 500, 1280, 720], fill=(85, 170, 85))

            for idx, anim_name in enumerate(selected_animals[:8]):
                char_color = CHARACTERISTICS_DB[anim_name]["color"]
                cx = 30 + (idx % 4) * 300 + int(t*35 + idx*20) % 60
                cy = 280 + (idx // 4) * 170
                d.ellipse([cx, cy, cx+130, cy+100], fill=char_color, outline=(0,0,0), width=3)
                d.ellipse([cx+80, cy-30, cx+150, cy+40], fill=char_color, outline=(0,0,0), width=3)
                d.ellipse([cx+95, cy-5, cx+110, cy+10], fill=(0,0,0))
                d.ellipse([cx+120, cy-5, cx+135, cy+10], fill=(0,0,0))
                d.text((cx, cy+105), anim_name, fill=(255, 255, 255))

            d.text((20, 15), f"{selected_model[:90]}", fill=(255, 255, 0))
            return np.array(img)

        try:
            audio_clip = AudioFileClip("voice.mp3")
            video_clip = VideoClip(make_frame, duration=audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            video_clip.write_videofile("final_jungle.mp4", fps=24, codec='libx264', audio_codec='aac', logger=None)
            st.video("final_jungle.mp4")
            with open("final_jungle.mp4", "rb") as f:
                st.download_button("📥 DOWNLOAD VIDEO MP4", f, file_name="Cocomelon_AtoZ_English.mp4", mime="video/mp4", use_container_width=True)
            st.balloons()
            st.success(f"Video Ready! {len(selected_animals)} Animals Visible - Model: {selected_model}")
        except Exception as e:
            st.error(f"Video Error: {e}")
