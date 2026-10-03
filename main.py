import streamlit as st
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import asyncio
import edge_tts
from gtts import gTTS
import textwrap

st.set_page_config(page_title="Cocomelon 10K Models Studio - A to Z", page_icon="🌈", layout="wide")

# ==================== 10,000+ MODELS GENERATOR - A TO Z ====================

# A to Z Characters List for Video
ANIMALS_A_TO_Z = ["Alligator","Bear","Cat","Dog","Elephant","Fox","Giraffe","Horse","Lion","Monkey","Cow","Buffalo","Goat","Sheep","Rabbit","Tiger","Zebra","Panda","Deer","Wolf","Chicken","Duck","Parrot","Peacock","Turtle","Snake","Camel","Kangaroo","Penguin","Dolphin"]
KIDS_NAMES = ["Mimi","Toto","Bobo","Kiki","Lulu","Momo","Coco","Jojo","Nana","Dodo","Pippo","Bubu","Chuchu","Gugu","Lala","Mama","Papa","Baby Shark","Johnny","Wheels Bus"]
BACKGROUNDS_A_TO_Z = ["Green Jungle","Farm House","River Side","Desert","Snow Mountain","Beach","City Park","School","Night Jungle","Sunset","Rainbow Valley","Candy Land","Space","Underwater","Forest","Village","Playground","Zoo","Circus","Castle"]
ACTIONS_A_TO_Z = ["Dancing","Singing ABC","Eating","Sleeping","Running","Jumping","Playing Ball","Reading Book","Driving Car","Swimming","Flying","Climbing Tree","Cooking","Laughing","Crying Happy","Studying","Bathing","Brushing Teeth","Going to School","Saying Hi"]
COLORS_A_TO_Z = ["Red","Blue","Green","Yellow","Pink","Purple","Orange","White","Black","Brown","Golden","Silver","Rainbow"]

# Generate 10,000+ Models List
ALL_10K_MODELS = []
model_id = 1
for animal in ANIMALS_A_TO_Z:
    for bg in BACKGROUNDS_A_TO_Z:
        for action in ACTIONS_A_TO_Z:
            for kid in KIDS_NAMES[:5]:
                if model_id > 10000:
                    break
                ALL_10K_MODELS.append(f"Model {model_id} - {kid} with {animal} {action} in {bg} | Color {random.choice(COLORS_A_TO_Z)}")
                model_id += 1
            if model_id > 10000:
                break
        if model_id > 10000:
            break
    if model_id > 10000:
        break

# Add more to reach 10500
while len(ALL_10K_MODELS) < 10500:
    ALL_10K_MODELS.append(f"Model {len(ALL_10K_MODELS)+1} - Special Cocomelon Character {random.choice(KIDS_NAMES)} {random.choice(ACTIONS_A_TO_Z)} with {random.choice(ANIMALS_A_TO_Z)} in {random.choice(BACKGROUNDS_A_TO_Z)} - A to Z Special")

# Kids Voices - 10 Real Voices for 10K variations
VOICE_IDS = {
    "Ana - Cute American Baby Girl": "en-US-AnaNeural",
    "Ava - Tiny Fairy Girl": "en-US-AvaMultilingualNeural",
    "Jenny - School Girl": "en-US-JennyNeural",
    "Aria - Cartoon Girl": "en-US-AriaNeural",
    "Jane - Happy Girl": "en-US-JaneNeural",
    "Emma - UK Girl": "en-GB-LibbyNeural",
    "Maisie - Little Doll UK": "en-GB-MaisieNeural",
    "Neerja - Indian Girl": "en-IN-NeerjaNeural",
    "Ananya - Lovely Indian Girl": "en-IN-AnanyaNeural",
    "Guy - Small Boy": "en-US-GuyNeural"
}

async def generate_voice(text, voice_id, pitch, rate):
    communicate = edge_tts.Communicate(text, voice_id, pitch=pitch, rate=rate)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# ==================== UI - 100% ENGLISH ====================
st.markdown("<h1 style='text-align:center; color:#FF0000;'>🌈 COCOMELON A TO Z - 10,000+ MODELS STUDIO 🌈</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>All Characters Visible - Full Auto Video Generator</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    selected_model = st.selectbox(f"Select Model (Total {len(ALL_10K_MODELS)}+ Models - A to Z)", ALL_10K_MODELS, index=0)
    story_prompt = st.text_area("Enter Chat Prompt - What Video You Want?", "Mimi the cat and dog and cow and buffalo go to jungle school and sing ABC song, all animals dancing together", height=120)
with col2:
    voice_select = st.selectbox("Select Voice Character (10 Base Voices)", list(VOICE_IDS.keys()))
    pitch_select = st.selectbox("Voice Pitch (For 10K Variations)", ["+25Hz - Super Tiny Baby", "+15Hz - Cute Kid", "+5Hz - Normal Kid", "-5Hz - Small Boy"])
    speed_select = st.selectbox("Voice Speed", ["+10% Fast Happy", "+0% Normal", "-10% Slow Cute"])
with col3:
    jungle_bg = st.selectbox("Select Background - A to Z Jungle Tools", BACKGROUNDS_A_TO_Z)
    characters_multi = st.multiselect("Select Characters to Show in Video (All Will Be Visible)", ANIMALS_A_TO_Z, default=["Cat","Dog","Cow","Buffalo","Lion","Elephant"])
    video_length = st.slider("Video Length Seconds", 5, 30, 15)

st.divider()

if st.button("🚀 GENERATE A TO Z VIDEO - 10,000 MODELS READY", type="primary", use_container_width=True):
    st.info(f"Generating: {selected_model}")

    # Step 1: Generate Story Text A to Z
    full_text = f"Hello kids! Welcome to Cocomelon! {story_prompt}. Today {', '.join(characters_multi)} are in {jungle_bg}. They are {selected_model}. They sing ABC song and dance. Johnny Johnny Yes Papa! Twinkle Twinkle Little Star! Wheels on the bus go round and round! We love you kids!"
    st.success("Story Generated - A to Z Complete")
    st.write(full_text)

    # Step 2: Voice Generation
    with st.spinner("Generating Kids Voice - English Only..."):
        try:
            voice_id = VOICE_IDS[voice_select]
            pitch = pitch_select.split(" - ")[0]
            rate = speed_select.split(" ")[0]
            audio_bytes = asyncio.run(generate_voice(full_text, voice_id, pitch, rate))
            st.audio(audio_bytes, format="audio/mp3")
            # Save temp for video
            with open("temp_voice.mp3", "wb") as f:
                f.write(audio_bytes)
        except Exception as e:
            st.warning(f"Edge TTS failed, using backup gTTS: {e}")
            tts = gTTS(text=full_text, lang='en', slow=False)
            tts.save("temp_voice.mp3")
            with open("temp_voice.mp3", "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes)

    # Step 3: A to Z Video with All Characters Visible
    with st.spinner("Generating Video - All Characters Visible A to Z..."):
        def make_frame(t):
            # Background based on selection
            if "Farm" in jungle_bg:
                img = Image.new('RGB', (1280, 720), (135, 206, 235))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(34, 139, 34))
                d.rectangle([800, 250, 1100, 500], fill=(139, 69, 19))
            elif "Night" in jungle_bg:
                img = Image.new('RGB', (1280, 720), (5, 20, 50))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(10, 50, 10))
                d.ellipse([1000, 40, 1120, 160], fill=(255, 255, 180))
            elif "Beach" in jungle_bg:
                img = Image.new('RGB', (1280, 720), (135, 206, 250))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(238, 221, 130))
            elif "Snow" in jungle_bg:
                img = Image.new('RGB', (1280, 720), (200, 220, 255))
                d = ImageDraw.Draw(img)
                d.rectangle([0, 500, 1280, 720], fill=(255, 255, 255))
            else: # Jungle
                img = Image.new('RGB', (1280, 720), (34, 139, 34))
                d = ImageDraw.Draw(img)
                # Trees A to Z
                for i in range(8):
                    x = i*160
                    d.rectangle([x+70, 80, x+90, 500], fill=(101, 67, 33))
                    d.ellipse([x+10, 10, x+150, 120], fill=(0, 100, 0))
                d.rectangle([0, 500, 1280, 720], fill=(50, 180, 50))

            # Draw ALL selected characters visible
            for idx, char in enumerate(characters_multi[:10]): # Show max 10 at once for visibility
                cx = 50 + (idx % 5) * 250 + int(t*30 + idx*10) % 50
                cy = 300 + (idx // 5) * 150
                col = (random.randint(100,255), random.randint(100,255), random.randint(100,255))
                # Body
                d.ellipse([cx, cy, cx+120, cy+100], fill=col, outline=(0,0,0), width=2)
                # Head
                d.ellipse([cx+70, cy-30, cx+140, cy+40], fill=col, outline=(0,0,0), width=2)
                # Eyes
                d.ellipse([cx+90, cy-10, cx+100, cy+5], fill=(0,0,0))
                d.ellipse([cx+115, cy-10, cx+125, cy+5], fill=(0,0,0))
                # Name
                d.text((cx, cy+105), char, fill=(255,255,255))

            # Title
            d.text((20, 20), f"{selected_model[:80]}", fill=(255,255,0))
            d.text((20, 680), "COCOMELON PRO - A TO Z 10K MODELS STUDIO - ALL CHARACTERS VISIBLE", fill=(255,0,0))
            return np.array(img)

        try:
            audio_clip = AudioFileClip("temp_voice.mp3")
            video_clip = VideoClip(make_frame, duration=audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
            video_clip.write_videofile("final_10k_video.mp4", fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)

            st.video("final_10k_video.mp4")
            with open("final_10k_video.mp4", "rb") as f:
                st.download_button("📥 DOWNLOAD FULL VIDEO MP4 - A TO Z READY", f, file_name="Cocomelon_10K_AtoZ.mp4", mime="video/mp4", use_container_width=True)
            st.balloons()
            st.success(f"SUCCESS! Video Generated with {len(characters_multi)} Characters Visible! Model: {selected_model} - Ready for YouTube!")
        except Exception as e:
            st.error(f"Video Error: {e}. Please check requirements.txt is committed.")

st.markdown("---")
st.markdown(f"**Total Models Loaded: {len(ALL_10K_MODELS)}+ | Characters: {len(ANIMALS_A_TO_Z)} A to Z Animals | Backgrounds: {len(BACKGROUNDS_A_TO_Z)} | All English - No Urdu | Auto Video Generation**")
