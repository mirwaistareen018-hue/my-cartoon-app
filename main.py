import streamlit as st
import requests
import io
from PIL import Image, ImageDraw
import numpy as np
import asyncio
import edge_tts
from gtts import gTTS
from moviepy.editor import VideoClip, AudioFileClip, CompositeAudioClip
import random

st.set_page_config(page_title="Cocomelon AI Brain", page_icon="🧠", layout="wide")
st.markdown("<h1 style='text-align:center;color:red;'>🧠 COCOMELON - AI BRAIN AUTO SYSTEM 🧠</h1>", unsafe_allow_html=True)

MODELS = [f"Model {i} - Auto AI Brain" for i in range(1, 10001)]
VOICES = {"Ana - Baby Girl": "en-US-AnaNeural"}

# --- AI BRAIN FUNCTION ---
def ai_brain_generate_image(prompt_text):
    try:
        # Free AI Image API - No Key Needed
        url = f"https://image.pollinations.ai/prompt/{prompt_text}?width=512&height=512&nologo=true&model=turbo"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            return img
    except Exception as e:
        st.warning(f"AI Image Error: {e}")
    return None

async def make_voice(text, vid):
    comm = edge_tts.Communicate(text, vid, pitch="+18Hz", rate="+0%")
    data = b""
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]
    return data

def extract_animals_from_story(story):
    story_lower = story.lower()
    found = []
    keywords = {
        "cat": "cat", "billi": "cat", "wolf": "cat",
        "mouse": "mouse", "chuha": "mouse", "rat": "mouse",
        "dog": "dog", "cow": "cow", "buffalo": "buffalo",
        "lion": "lion", "elephant": "elephant", "rabbit": "rabbit"
    }
    for key, animal in keywords.items():
        if key in story_lower and animal not in found:
            found.append(animal)
    if not found:
        found = ["mouse", "cat"]
    return found[:3]

# --- UI ---
c1, c2 = st.columns(2)
with c1:
    model = st.selectbox("Select Model (10000+)", MODELS)
    story = st.text_area("Story Prompt - AI Brain Will Auto Understand", "Mouse is eating cheese inside small door house, big gray wolf cat comes running fast to catch mouse, mouse gets scared", height=120)
with c2:
    voice_name = st.selectbox("Voice", list(VOICES.keys()))
    music_file = st.file_uploader("Background Music MP3 (Optional)", type=["mp3","wav"])
    st.info("🧠 AI Brain: Aap sirf kahani likho, AI khud characters bana lega!")

if st.button("🚀 GENERATE WITH AI BRAIN - AUTO", type="primary", use_container_width=True):
    st.write(f"**Story:** {story}")

    # Step 1: AI Brain Understands Story
    with st.spinner("🧠 AI Brain Soch Raha Hai... Characters Samajh Raha Hai..."):
        characters = extract_animals_from_story(story)
        st.success(f"🧠 AI Brain Ne Samjha: Isko chahiye {', '.join(characters)}")

    # Step 2: AI Brain Generates Images
    generated_images = {}
    with st.spinner(f"🎨 AI Brain Images Bana Raha Hai: {characters}"):
        for char in characters:
            prompt_3d = f"cute 3d pixar cartoon {char}, big eyes, soft fur, tom and jerry style, white background, high quality, 3d render"
            img = ai_brain_generate_image(prompt_3d)
            if img:
                generated_images[char] = img
                st.image(img, caption=f"AI Generated: {char}", width=150)

    # Step 3: Voice
    with st.spinner("🎤 Voice Bana Raha Hai..."):
        full_text = f"Hello kids! {story}. This is {model}"
        try:
            audio_bytes = asyncio.run(make_voice(full_text, VOICES[voice_name]))
            open("voice.mp3","wb").write(audio_bytes)
        except:
            gTTS(full_text, lang='en').save("voice.mp3")
        st.audio("voice.mp3")

    # Step 4: Video with Auto Images
    def make_frame(t):
        # House background like your video
        img_bg = Image.new('RGB', (1280, 720), (240, 230, 140))
        d = ImageDraw.Draw(img_bg)
        d.rectangle([0,0,1280,500], fill=(245,245,245))
        d.rectangle([0,500,1280,720], fill=(240,230,140))
        d.rectangle([500,250,650,500], fill=(255,255,200), outline=(100,180,180), width=8)

        # Paste AI generated characters with auto movement
        for idx, (char_name, char_img) in enumerate(generated_images.items()):
            char_img_resized = char_img.resize((220, 220))
            if idx == 0: # First character - static near door
                x, y = 480, 350
            else: # Second character - running like your video
                x = int(1100 - (t*180) % 1300)
                y = 300 + int(abs(np.sin(t*3))*20)

            # Paste with transparency
            temp_bg = Image.new('RGBA', (1280,720), (0,0,0,0))
            temp_bg.paste(char_img_resized, (x, y), char_img_resized)
            img_bg = Image.alpha_composite(img_bg.convert('RGBA'), temp_bg).convert('RGB')

        return np.array(img_bg)

    try:
        voice_clip = AudioFileClip("voice.mp3")
        if music_file:
            open("bg.mp3","wb").write(music_file.getbuffer())
            bg_clip = AudioFileClip("bg.mp3")
            if bg_clip.duration < voice_clip.duration:
                bg_clip = bg_clip.loop(duration=voice_clip.duration)
            else:
                bg_clip = bg_clip.subclip(0, voice_clip.duration)
            final_audio = CompositeAudioClip([voice_clip, bg_clip.volumex(0.18)])
        else:
            final_audio = voice_clip

        video = VideoClip(make_frame, duration=voice_clip.duration).set_audio(final_audio)
        video.write_videofile("final.mp4", fps=24, codec='libx264', audio_codec='aac', logger=None)
        st.video("final.mp4")
        with open("final.mp4","rb") as f:
            st.download_button("📥 DOWNLOAD AI BRAIN VIDEO", f, file_name="AI_Brain_Cartoon.mp4", mime="video/mp4", use_container_width=True)
        st.balloons()
        st.success(f"🧠 AI Brain Ne Khud {len(generated_images)} Characters Bana Kar Video Bana Di!")
    except Exception as e:
        st.error(f"Error: {e}")
