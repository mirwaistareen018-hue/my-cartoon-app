import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import random, os, time
from gtts import gTTS
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip

st.set_page_config(page_title="COCOMELON VIDEO APP", layout="wide")
st.title("Talking Video Generator")
st.success("App is Working - Video Mode ON")

def get_image(prompt, retries=3):
    for attempt in range(retries):
        try:
            q = requests.utils.quote(prompt)
            seed = random.randint(1, 999999)
            # Try pollinations with cache bust
            url = f"https://image.pollinations.ai/prompt/{q}?width=1024&height=576&seed={seed}&nologo=true"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=60)
            if r.status_code == 200 and len(r.content) > 5000:
                img = Image.open(BytesIO(r.content)).convert("RGB")
                w, h = img.size
                # crop watermark
                if h > 30:
                    img = img.crop((0, 0, w, h-25))
                return img
        except Exception as e:
            st.warning(f"Attempt {attempt+1} failed, retrying...")
            time.sleep(2)
    return None

story_text = st.text_area("Write Story Script:", "A small cute mouse is eating cheese on the table, then a big cat comes")
lang = st.selectbox("Select Voice Language", ["en", "ur"])
btn = st.button("GENERATE VIDEO")

if btn:
    if not story_text.strip():
        st.error("Please write story first")
    else:
        with st.spinner("Generating Images... This may take 60 seconds..."):
            prompts = [
                f"cute 3d pixar baby mouse eating cheese on table, warm light, {story_text}",
                f"big fluffy cat entering room looking at mouse, 3d pixar style",
                f"cute mouse running away scared from cat, 3d pixar style"
            ]
            
            temp_images = []
            for i, p in enumerate(prompts):
                st.write(f"Generating Scene {i+1}...")
                img = get_image(p)
                if img:
                    st.image(img, caption=f"Scene {i+1}")
                    path = f"/tmp/scene_{i}.jpg"
                    img.save(path)
                    temp_images.append(path)
                else:
                    st.error(f"Scene {i+1} failed")

            if len(temp_images) >= 1:
                st.write("Generating Voice and Video...")
                try:
                    # Voice
                    tts = gTTS(text=story_text, lang=lang, slow=False)
                    tts.save("/tmp/voice.mp3")
                    voice_clip = AudioFileClip("/tmp/voice.mp3")

                    # Video clip - each image shows for equal time
                    clip = ImageSequenceClip(temp_images, fps=1)
                    clip = clip.set_duration(voice_clip.duration)

                    # Background music if exists
                    if os.path.exists("song.mp3"):
                        try:
                            bg_music = AudioFileClip("song.mp3").subclip(0, voice_clip.duration).volumex(0.15)
                            final_audio = CompositeAudioClip([voice_clip, bg_music])
                        except:
                            final_audio = voice_clip
                    else:
                        final_audio = voice_clip

                    final_clip = clip.set_audio(final_audio)
                    final_clip.write_videofile("/tmp/final_video.mp4", fps=24, codec='libx264', audio_codec='aac', logger=None)
                    
                    st.video("/tmp/final_video.mp4")
                    with open("/tmp/final_video.mp4", "rb") as f:
                        st.download_button("Download Video", f, file_name="cocomelon_video.mp4")
                    st.balloons()
                    st.success("Video Ready!")
                except Exception as e:
                    st.error(f"Video error: {e}")
            else:
                st.error("Failed to generate images, please try again. Server is busy, press GENERATE VIDEO again.")
