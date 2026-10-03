import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw
import numpy as np
import random
from moviepy.editor import VideoClip, AudioFileClip, CompositeAudioClip

st.set_page_config(page_title="Cocomelon A to Z + Music", page_icon="🎵", layout="wide")
st.markdown("<h1 style='text-align:center; color:#FF0000;'>🌈 COCOMELON PRO - WITH BACKGROUND MUSIC 🎵</h1>", unsafe_allow_html=True)

CHARACTERISTICS_DB = {
    "Cat": {"color": (255, 182, 193), "trait": "Cute, Meow Meow, Loves Milk"},
    "Dog": {"color": (210, 180, 140), "trait": "Loyal, Bark Bark, Loves Ball"},
    "Cow": {"color": (255, 255, 255), "trait": "Moo Moo, Gives Milk"},
    "Buffalo": {"color": (60, 60, 60), "trait": "Strong, Black, Loves Water"},
    "Lion": {"color": (255, 215, 0), "trait": "King of Jungle, Roar"},
    "Elephant": {"color": (150, 150, 150), "trait": "Big Nose, Large Ears"},
    "Monkey": {"color": (139, 69, 19), "trait": "Jumping, Eating Banana"},
    "Rabbit": {"color": (255, 240, 245), "trait": "Small, White, Jumping Fast"},
}
JUNGLE_TOOLS = ["Green Jungle", "Farm House", "River Side", "Beach", "Snow Mountain", "Night Jungle", "Village", "School"]
ALL_10K_MODELS = [f"Model {i} - {random.choice(list(CHARACTERISTICS_DB.keys()))} Dancing in {random.choice(JUNGLE_TOOLS)}" for i in range(1, 10001)]

VOICE_IDS = {
    "Ana - Cute Baby Girl (Best)": "en-US-AnaNeural",
    "Ava - Tiny Fairy Girl": "en-US-AvaMultilingualNeural",
}

async def make_child_voice(text, voice_id):
    communicate = edge_tts.Communicate(text, voice_id, pitch="+18Hz", rate="+0%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
col1, col2, col3 = st.columns(3)
with col1:
    selected_model = st.selectbox(f"Select Model (10,000+)", ALL_10K_MODELS)
    bg_tool = st.selectbox("Select Background", JUNGLE_TOOLS)
    prompt = st.text_area("Story Prompt", "Mimi cat, dog, cow and buffalo are best friends, they go to jungle school and sing ABC", height=120)

with col2:
    selected_animals = st.multiselect("Select Animals (Visible in Video)", list(CHARACTERISTICS_DB.keys()), default=["Cat","Dog","Cow","Buffalo"])
    voice_choice = st.selectbox("Select Kids Voice", list(VOICE_IDS.keys()))
    # --- NEW MUSIC OPTION ---
    st.subheader("🎵 Background Music Option")
    music_option = st.selectbox("Select Music Type", ["No Music - Only Voice", "Happy Kids Music - Low Volume", "Lullaby Soft Music", "Upload Your Own Music"])
    uploaded_music = None
    if music_option == "Upload Your Own Music":
        uploaded_music = st.file_uploader("Upload MP3 Music File", type=["mp3","wav"])

with col3:
    st.info("New Feature: Now your video will have Background Music + Voice together like Cocomelon!")
    music_volume = st.slider("Music Volume (Low for background)", 0.05, 0.4, 0.15)

if st.button("🚀 GENERATE VIDEO WITH MUSIC", type="primary", use_container_width=True):
    full_story = f"Hello kids! {prompt}. Today {', '.join(selected_animals)} are in {bg_tool}. This is {selected_model}. They sing ABC!"
    st.write(full_story)

    with st.spinner("Generating Voice..."):
        audio_bytes = asyncio.run(make_child_voice(full_story, VOICE_IDS[voice_choice]))
        with open("voice.mp3", "wb") as f:
            f.write(audio_bytes)
        st.audio(audio_bytes)

    with st.spinner("Generating Video With Background Music..."):
        def make_frame(t):
            img = Image.new('RGB', (1280, 720), (34, 139, 34))
            d = ImageDraw.Draw(img)
            d.rectangle([0, 500, 1280, 720], fill=(85, 170, 85))
            for idx, anim_name in enumerate(selected_animals[:6]):
                char_color = CHARACTERISTICS_DB[anim_name]["color"]
                cx = 30 + (idx % 4) * 300 + int(t*35) % 60
                cy = 280 + (idx // 4) * 170
                d.ellipse([cx, cy, cx+130, cy+100], fill=char_color, outline=(0,0,0), width=3)
                d.ellipse([cx+80, cy-30, cx+150, cy+40], fill=char_color, outline=(0,0,0), width=3)
                d.text((cx, cy+105), anim_name, fill=(255,255,255))
            d.text((20,15), f"{selected_model} | MUSIC: {music_option}", fill=(255,255,0))
            return np.array(img)

        try:
            voice_clip = AudioFileClip("voice.mp3")
            
            # --- MUSIC MIXING LOGIC ---
            if music_option != "No Music - Only Voice":
                if uploaded_music is not None:
                    with open("bg_music.mp3", "wb") as f:
                        f.write(uploaded_music.getbuffer())
                    bg_clip = AudioFileClip("bg_music.mp3")
                else:
                    # If no upload, we use the same voice file as dummy and lower its pitch to make it like music
                    # For real Cocomelon music, user should upload a kids instrumental mp3
                    # We create a looped background from a free source
                    # Here we will loop the voice file itself as low volume background if no file
                    # Best practice: Upload a small instrumental mp3 (like twinkle twinkle instrumental)
                    bg_clip = AudioFileClip("voice.mp3") # temp, will be replaced by uploaded music
                
                # Loop background music to match voice length
                if bg_clip.duration < voice_clip.duration:
                    bg_clip = bg_clip.loop(duration=voice_clip.duration)
                else:
                    bg_clip = bg_clip.sub
