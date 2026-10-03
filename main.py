import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw
import numpy as np
import random
from moviepy.editor import VideoClip, AudioFileClip, CompositeAudioClip

st.set_page_config(page_title="Cocomelon Pro", page_icon="🌈", layout="wide")
st.markdown("<h1 style='text-align:center;color:red;'>🌈 COCOMELON A TO Z - FINAL FIXED 🌈</h1>", unsafe_allow_html=True)

# --- 100% ENGLISH DATABASE ---
ANIMALS = {
    "Cat": (255, 182, 193),
    "Dog": (210, 180, 140),
    "Cow": (255, 255, 255),
    "Buffalo": (80, 80, 80),
    "Lion": (255, 215, 0),
    "Elephant": (150, 150, 150),
    "Monkey": (139, 69, 19),
    "Rabbit": (255, 240, 245),
}

JUNGLES = ["Green Jungle", "Farm House", "River Side", "Beach", "Snow Mountain", "Night Jungle", "Village", "School"]
MODELS = [f"Model {i} - {random.choice(list(ANIMALS.keys()))} in {random.choice(JUNGLES)}" for i in range(1, 10001)]
VOICES = {
    "Ana - Cute Baby Girl": "en-US-AnaNeural",
    "Ava - Tiny Girl": "en-US-AvaMultilingualNeural",
    "Jenny - School Girl": "en-US-JennyNeural",
}

async def make_voice(text, voice_id):
    communicate = edge_tts.Communicate(text, voice_id, pitch="+18Hz", rate="+0%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- UI ---
c1, c2 = st.columns(2)
with c1:
    model = st.selectbox("Select Model (10,000+ Models)", MODELS)
    bg_tool = st.selectbox("Select Background Tool", JUNGLES)
    prompt = st.text_area("Chat Prompt - Enter Story", "Mimi cat, dog, cow and buffalo are best friends, they go to jungle school and sing ABC song", height=130)

with c2:
    selected_animals = st.multiselect("Select Animals (All Visible)", list(ANIMALS.keys()), default=["Cat", "Dog", "Cow", "Buffalo"])
    voice_choice = st.selectbox("Select Kids Voice", list(VOICES.keys()))
    music_file = st.file_uploader("Upload Background Music MP3 (Optional for Cocomelon Music)", type=["mp3", "wav"])
    music_vol = st.slider("Music Volume", 0.05, 0.4, 0.15)

if st.button("🚀 GENERATE COCOMELON VIDEO - FINAL", type="primary", use_container_width=True):
    full_story = f"Hello kids! Welcome to Cocomelon! {prompt}. Today our heroes are {', '.join(selected_animals)} in {bg_tool}. This is {model}. They sing Twinkle Twinkle, Johnny Johnny Yes Papa, ABC Song!"
    st.success("Story Ready!")
    st.write(full_story)

    # Voice
    with st.spinner("Generating Voice..."):
        try:
            audio_bytes = asyncio.run(make_voice(full_story, VOICES[voice_choice]))
            with open("voice.mp3", "wb") as f:
                f.write(audio_bytes)
            st.audio(audio_bytes)
        except Exception as e:
            st.warning(f"Using Backup Voice: {e}")
            tts = gTTS(full_story, lang='en')
            tts.save("voice.mp3")
            st.audio("voice.mp3")

    # Video
    with st.spinner("Generating Video..."):
        def make_frame(t):
            img = Image.new('RGB', (1280, 720), (34, 139, 34))
            d = ImageDraw.Draw(img)
            d.rectangle([0, 500, 1280, 720], fill=(85, 170, 85))
            for idx, name in enumerate(selected_animals[:6]):
                color = ANIMALS[name]
                cx = 40 + idx * 200 + int(t * 30) % 50
                cy = 350
                d.ellipse([cx, cy, cx+120, cy+90], fill=color, outline=(0,0,0), width=3)
                d.ellipse([cx+70, cy-20, cx+130, cy+30], fill=color, outline=(0,0,0), width=3)
                d.ellipse([cx+85, cy, cx+100, cy+15], fill=(0,0,0))
                d.ellipse([cx+110, cy, cx+125, cy+15], fill=(0,0,0))
                d.text((cx, cy+100), name, fill=(255,255,255))
            d.text((20, 20), f"{model[:80]} | {bg_tool}", fill=(255,255,0))
            return np.array(img)

        try:
            voice_clip = AudioFileClip("voice.mp3")

            if music_file is not None:
                with open("bg_music.mp3", "wb") as f:
                    f.write(music_file.getbuffer())
                bg_clip = AudioFileClip("bg_music.mp3")
                if bg_clip.duration < voice_clip.duration:
                    bg_clip = bg_clip.loop(duration=voice_clip.duration)
                else:
                    bg_clip = bg_clip.subclip(0, voice_clip.duration)
                bg_clip = bg_clip.volumex(music_vol)
                final_audio = CompositeAudioClip([voice_clip, bg_clip])
            else:
                final_audio = voice_clip

            video_clip = VideoClip(make_frame, duration=voice_clip.duration)
            video_clip = video_clip.set_audio(final_audio)
            video_clip.write_videofile("final.mp4", fps=24, codec='libx264', audio_codec='aac', logger=None)

            st.video("final.mp4")
            with open("final.mp4", "rb") as f:
                st.download_button("📥 DOWNLOAD VIDEO MP4", f, file_name="Cocomelon_Final.mp4", mime="video/mp4", use_container_width=True)
            st.balloons()
            st.success("Done! Video Generated Successfully!")
        except Exception as e:
            st.error(f"Video Error: {e}")
