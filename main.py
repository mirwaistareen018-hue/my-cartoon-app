import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import random, os
from gtts import gTTS
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip

st.set_page_config(page_title="COCOMELON VIDEO APP", layout="wide")
st.title("COCOMELON Talking Video Generator")
st.success("App is Working - Video Mode ON")

def get_image(prompt):
    try:
        q = requests.utils.quote(prompt)
        seed = random.randint(1, 99999)
        url = f"https://image.pollinations.ai/prompt/{q}?width=1024&height=576&nologo=true&seed={seed}"
        r = requests.get(url, timeout=40)
        img = Image.open(BytesIO(r.content))
        w, h = img.size
        return img.crop((0, 0, w, h-30))
    except Exception as e:
        return None

story_text = st.text_area("Write Story Script:", "A small cute mouse is eating cheese on the table, then a big cat comes")
lang = st.selectbox("Select Voice Language", ["en", "ur"])
btn = st.button("GENERATE VIDEO")

if btn:
    with st.spinner("Generating Video... Please wait 1 minute..."):
        prompts = [
            f"cute 3d pixar baby mouse {story_text}, eating cheese on table, warm light",
            f"big fluffy cat entering room, looking at mouse, 3d pixar style",
            f"cute mouse running away scared, 3d pixar style"
        ]
        
        temp_images = []
        for i, p in enumerate(prompts):
            img = get_image(p)
            if img:
                st.image(img, caption=f"Scene {i+1}: {p[:50]}")
                path = f"/tmp/scene_{i}.jpg"
                img.save(path)
                temp_images.append(path)

        if len(temp_images) >= 2:
            # Generate voice
            tts = gTTS(text=story_text, lang=lang, slow=False)
            tts.save("/tmp/voice.mp3")
            voice_clip = AudioFileClip("/tmp/voice.mp3")

            # Create video clip
            clip = ImageSequenceClip(temp_images, fps=1)
            clip = clip.set_duration(voice_clip.duration)

            # Background music
            if os.path.exists("song.mp3"):
                bg_music = AudioFileClip("song.mp3").subclip(0, voice_clip.duration).volumex(0.15)
                final_audio = CompositeAudioClip([voice_clip, bg_music])
            else:
                final_audio = voice_clip

            final_clip = clip.set_audio(final_audio)
            final_clip.write_videofile("/tmp/final_video.mp4", fps=24, codec='libx264', audio_codec='aac')

            st.video("/tmp/final_video.mp4")
            st.balloons()
            st.success("Video is Ready! Character is talking with background music.")
        else:
            st.error("Failed to generate images, please try again")
