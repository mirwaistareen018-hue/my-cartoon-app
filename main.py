"""
Story -> Cartoon MP4, all in one page (with AI story writer).

Install once:
    pip install -r requirements.txt

Run:
    python main.py
Open the link shown in the terminal.
Either paste your own story, or type an idea and press the AI story button.
Then press the video button. The finished MP4 appears below.
"""

import asyncio
import re
import tempfile
import time
import urllib.parse

import edge_tts
import gradio as gr
import requests
from deep_translator import GoogleTranslator
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    afx,
    concatenate_videoclips,
)

W, H = 1280, 720
STYLE = "cute colorful 3D cartoon for kids, soft lighting, simple bright background, "
SEED = 1234  # same seed helps keep the look similar across scenes
VOICES = {
    "اردو - لڑکی": "ur-PK-UzmaNeural",
    "اردو - لڑکا": "ur-PK-AsadNeural",
    "ہندی - لڑکی": "hi-IN-SwaraNeural",
    "ہندی - لڑکا": "hi-IN-MadhurNeural",
}


# ---------- AI: story writer (free text service, no key) ----------
def write_story(idea, voice_name, sentences):
    if not (idea or "").strip():
        raise gr.Error("پہلے کہانی کا خیال لکھیں")
    language = "Hindi" if "ہندی" in voice_name else "Urdu"
    prompt = (
        f"Write a short, simple, happy children's story in {language}. "
        f"Use exactly {int(sentences)} short sentences, each on its own line. "
        f"No title, no numbering, no extra text. Idea: {idea.strip()}"
    )
    url = "https://text.pollinations.ai/" + urllib.parse.quote(prompt)
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
    except Exception as e:
        raise gr.Error(f"کہانی نہیں بن سکی، دوبارہ کوشش کریں: {e}")
    return r.text.strip()


# ---------- Story -> scenes ----------
def split_story(text):
    scenes = []
    for line in text.splitlines():
        for part in re.split(r"(?<=[۔.!?؟])\s+", line.strip()):
            if part.strip():
                scenes.append(part.strip())
    return scenes


# ---------- AI: translation for picture prompts ----------
def to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception:
        return text


# ---------- AI: picture ----------
def make_image(description, path):
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(STYLE + description)
        + f"?width={W}&height={H}&nologo=true&seed={SEED}"
    )
    last_error = None
    for _ in range(3):
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            return
        except Exception as e:
            last_error = e
            time.sleep(3)
    raise gr.Error(f"تصویر نہیں بن سکی: {last_error}")


# ---------- AI: voice ----------
async def _tts(text, voice, path):
    await edge_tts.Communicate(text, voice).save(path)


# ---------- One scene = picture + voice + camera zoom ----------
def make_scene(sentence, character, voice, i, folder):
    img = f"{folder}/s{i}.jpg"
    aud = f"{folder}/s{i}.mp3"
    description = (character + ", " if character else "") + to_english(sentence)
    make_image(description, img)
    asyncio.run(_tts(sentence, voice, aud))
    audio = AudioFileClip(aud)
    d = audio.duration + 0.6
    clip = ImageClip(img).with_duration(d).resized(lambda t: 1 + 0.05 * t / d)
    clip = CompositeVideoClip([clip.with_position("center")], size=(W, H)).with_duration(d)
    return clip.with_audio(audio)


# ---------- Whole video ----------
def generate(story, character, voice_name, music, max_scenes, progress=gr.Progress()):
    scenes = split_story(story or "")[: int(max_scenes)]
    if not scenes:
        raise gr.Error("پہلے کہانی لکھیں")
    voice = VOICES[voice_name]
    folder = tempfile.mkdtemp()
    clips = []
    for i, sentence in enumerate(scenes):
        progress(i / len(scenes), desc=f"سین {i + 1} / {len(scenes)} بن رہا ہے")
        clips.append(make_scene(sentence, (character or "").strip(), voice, i, folder))

    progress(0.95, desc="ویڈیو جوڑی جا رہی ہے")
    video = concatenate_videoclips(clips, method="compose")
    if music:
        bg = AudioFileClip(music).with_effects(
            [afx.AudioLoop(duration=video.duration), afx.MultiplyVolume(0.12)]
        )
        video = video.with_audio(CompositeAudioClip([video.audio, bg]))
    out = f"{folder}/video.mp4"
    video.write_videofile(out, fps=24, codec="libx264", audio_codec="aac")
    return out


# ---------- One-page screen ----------
with gr.Blocks() as demo:
    gr.Markdown("# کہانی سے کارٹون ویڈیو")

    idea = gr.Textbox(label="کہانی کا خیال (اختیاری، AI کہانی لکھے گا)",
                      placeholder="ایک چھوٹا خرگوش جو دوستی کرنا سیکھتا ہے")
    sentences = gr.Slider(8, 30, value=16, step=1, label="کہانی کے جملے (تقریباً 2 منٹ = 16)")
    story_btn = gr.Button("AI سے کہانی لکھواؤ")

    story = gr.Textbox(lines=10, label="کہانی (خود پیسٹ کریں یا AI والی ایڈٹ کریں)")
    character = gr.Textbox(
        label="کردار کی تفصیل (انگریزی میں، اختیاری)",
        placeholder="a small brown rabbit with big ears and a blue scarf",
    )
    voice = gr.Dropdown(list(VOICES), value="اردو - لڑکی", label="آواز")
    music = gr.Audio(type="filepath", label="بیک گراؤنڈ میوزک (اختیاری)")
    max_scenes = gr.Slider(1, 60, value=20, step=1, label="زیادہ سے زیادہ سین")

    btn = gr.Button("ویڈیو بناؤ", variant="primary")
    vid = gr.Video(label="تیار ویڈیو (MP4)")

    story_btn.click(write_story, [idea, voice, sentences], story)
    btn.click(generate, [story, character, voice, music, max_scenes], vid)

demo.launch()
