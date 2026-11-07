"""Montage of the three site videos from the Google Flow clips.

For every video:
  1. title cards and caption images are drawn as HTML and captured with headless Chrome (Arabic text with the Cairo font)
  2. the voice-over is a recorded narration (one file per video) cut into sentences at its pauses;
     a video without a recording falls back to the macOS Arabic voice (say -v Majed).
     The audio watermark (sound logo) plays over the closing logo card
  3. a soft background track is synthesised with NumPy (chords + a light arpeggio)
  4. ffmpeg joins the clips with cross-fades, overlays the captions at the same time as the voice,
     and the audio (clip ambience + music + voice, music lowered under the voice) is mixed with NumPy
  5. a WebVTT file with the same timings is written for the <track> element of the page

usage:  SRC=../../source_media python3 make_videos.py
"""
import json
import os
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = Path(os.environ.get("SRC", HERE / ".." / ".." / "source_media")).resolve()
OUT = (HERE / ".." / "assets" / "video").resolve()
LOGO = (HERE / ".." / "assets" / "logo" / "logo-light.svg").resolve()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H, FPS, SR = 1280, 720, 24, 44100
XF = 0.6                                  # cross-fade length (s)
TMP = Path(tempfile.mkdtemp(prefix="sl_video_"))

# each scene: (kind, source, seconds, spoken text, caption text)
VIDEOS = {
    "intro": {
        "title": "تعرّف على Smart Land", "subtitle": "حلول برمجية ذكية منذ 2011",
        "scenes": [
            ("clip", "v1_c1_city.mp4", 8, "منذ عام ألفين وأحد عشر، تحوّل سمارت لاند الأفكار إلى حلول برمجية",
             "منذ عام 2011، تحوّل Smart Land الأفكار إلى حلول برمجية"),
            ("clip", "v1_c2_office.mp4", 8, "فريق من المهندسين يبني أنظمة مخصصة لقطاعات مختلفة",
             "فريق من المهندسين يبني أنظمة مخصصة لقطاعات مختلفة"),
            ("clip", "v1_c3_ai.mp4", 8, "والذكاء الاصطناعي في قلب كل منتج نصنعه",
             "والذكاء الاصطناعي في قلب كل منتج نصنعه"),
            ("clip", "v1_c4_team.mp4", 8, "نعمل مع عملائنا من الفكرة حتى الإطلاق",
             "نعمل مع عملائنا من الفكرة حتى الإطلاق"),
            ("clip", "v1_c5_handshake.mp4", 8, "سمارت لاند، شريكك التقني نحو المستقبل",
             "Smart Land، شريكك التقني نحو المستقبل"),
        ]},
    "smart-signal": {
        "title": "قصة نجاح: Smart Signal", "subtitle": "ترجمة لغة الإشارة بالذكاء الاصطناعي",
        "scenes": [
            ("clip", "v2_c1_signing.mp4", 8, "التواصل مع من لا يعرف لغة الإشارة تحدٍّ يومي للصم",
             "التواصل مع من لا يعرف لغة الإشارة تحدٍّ يومي للصم"),
            ("clip", "v2_c2_phone.mp4", 8, "تطبيق سمارت سيغنال يحوّل حركات اليدين إلى نص وصوت",
             "تطبيق Smart Signal يحوّل حركات اليدين إلى نص وصوت"),
            ("clip", "v2_c3_cafe.mp4", 8, "والنتيجة حوار طبيعي، في أي مكان",
             "والنتيجة حوار طبيعي، في أي مكان"),
        ]},
    "projects": {
        "title": "من مشاريعنا", "subtitle": "MyKey · Sada · Welcome",
        "scenes": [
            ("clip", "v3_c1_mykey.mp4", 8, "منصة ماي كي لإعلانات العقارات والمركبات، للبيع والإيجار",
             "منصة MyKey لإعلانات العقارات والمركبات، للبيع والإيجار"),
            ("clip", "v3_c2_sada.mp4", 8, "ومنصة صدى تجعل التعلم عن بعد تجربة تفاعلية",
             "ومنصة Sada تجعل التعلم عن بعد تجربة تفاعلية"),
            ("still", "img_welcome.jpg", 7, "وتطبيق ويلكم يجمع متاجر كثيرة في تطبيق تسوق واحد",
             "وتطبيق Welcome يجمع متاجر كثيرة في تطبيق تسوق واحد"),
        ]},
}
CARD_SEC, OUTRO_SEC = 3.0, 3.5

# recorded narration: file in SRC and the (start, end) of every sentence in seconds.
# The cut points are the pauses found with:  ffmpeg -i file -af silencedetect=noise=-38dB:d=0.25 -f null -
VOICE = {
    "intro": ("vo_intro.wav", [(0.00, 5.70), (6.33, 10.60), (11.33, 14.45), (15.23, 18.05), (18.73, 22.52)]),
    "smart-signal": ("vo_smart_signal.wav", [(0.20, 4.92), (5.48, 9.98), (10.62, 14.40)]),
}
WATERMARK = "watermark.wav"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def shot(html, png, transparent=False):
    """Draw an HTML page to a 1280x720 PNG with headless Chrome."""
    page = TMP / (png.stem + ".html")
    page.write_text(html, encoding="utf-8")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={TMP / 'chrome'}",
           f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={png}", page.as_uri()]
    if transparent:
        cmd.insert(3, "--default-background-color=00000000")
    run(cmd)


FONT = ('<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800&'
        'family=Montserrat:wght@600;800&display=swap" rel="stylesheet">')


def card_html(title, sub):
    return f"""<html dir="rtl"><head><meta charset="utf-8">{FONT}<style>
body{{margin:0;width:{W}px;height:{H}px;display:flex;flex-direction:column;align-items:center;justify-content:center;
background:radial-gradient(circle at 70% 30%,#0F766E 0,#0B1F3A 55%,#071426 100%);font-family:Cairo;color:#fff}}
object{{height:150px;margin-bottom:34px}} h1{{font-size:58px;margin:0;font-weight:800}}
p{{font-size:28px;margin:10px 0 0;color:#5EEAD4;font-weight:700}}</style></head>
<body><object data="{LOGO.as_uri()}"></object><h1>{title}</h1><p>{sub}</p></body></html>"""


def caption_html(text):
    return f"""<html dir="rtl"><head><meta charset="utf-8">{FONT}<style>
html,body{{margin:0;background:transparent;width:{W}px;height:{H}px}}
div{{position:absolute;bottom:46px;left:50%;transform:translateX(-50%);max-width:1040px;padding:10px 30px 14px;
background:rgba(7,20,38,.72);border-right:5px solid #2DD4BF;border-radius:12px;color:#fff;font:700 34px Cairo;
text-align:center;white-space:nowrap}}</style></head><body><div>{text}</div></body></html>"""


# ----------------------------------------------------------------------------- audio helpers
def read_wav(path):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return a.reshape(-1, w.getnchannels()).mean(axis=1)


def to_wav(src, dst, extra=()):
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), *extra, "-ac", "1", "-ar", str(SR), str(dst)])


def recorded(key, n):
    """sentence n of the recorded narration of video `key`"""
    file, cuts = VOICE[key]
    a, b = cuts[n]
    wav = TMP / f"{key}_rec{n}.wav"
    to_wav(SRC / file, wav, ["-ss", f"{a}", "-to", f"{b}", "-af",
                             f"highpass=f=80,afade=t=in:d=0.03,afade=t=out:st={b - a - 0.06:.2f}:d=0.06"])
    v = read_wav(wav)
    return v / np.abs(v).max() * 0.9


def voice(text, name):
    aiff = TMP / f"{name}.aiff"
    run(["say", "-v", "Majed", "-r", "182", "-o", str(aiff), text])
    wav = TMP / f"{name}.wav"
    # cut low rumble and even the level of the synthetic voice
    to_wav(aiff, wav, ["-af", "highpass=f=90,acompressor=threshold=-18dB:ratio=3:attack=5:release=120"])
    return read_wav(wav)


def music(seconds, seed):
    """Soft pad: Am - F - C - G chords (4 s each) plus a quiet arpeggio, made with NumPy."""
    t = np.arange(int(seconds * SR)) / SR
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
    out = np.zeros_like(t)
    rng = np.random.default_rng(seed)
    for k, start in enumerate(np.arange(0, seconds, 4.0)):
        notes = chords[k % 4]
        seg = (t >= start) & (t < start + 4.6)
        tt = t[seg] - start
        env = np.minimum(1, tt / 1.2) * np.minimum(1, (4.6 - tt) / 1.0)          # slow attack and release
        for f in notes:
            out[seg] += env * (np.sin(2 * np.pi * f / 2 * tt) * 0.5 + np.sin(2 * np.pi * f * 1.003 * tt) * 0.25)
        for j, f in enumerate(rng.permutation(notes * 2)[:4]):                    # arpeggio, 4 plucks per chord
            p = (t >= start + j) & (t < start + j + 1.5)
            tp = t[p] - start - j
            out[p] += 0.18 * np.exp(-tp * 3.0) * np.sin(2 * np.pi * f * 2 * tp)
    out *= np.minimum(1, t / 1.5) * np.minimum(1, (seconds - t) / 2.0)           # fade in / out
    return out / np.abs(out).max()


def write_wav(a, path):
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def vtt_time(s):
    return f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{s % 60:06.3f}"


# ----------------------------------------------------------------------------- one video
def build(key, spec):
    wm = None
    if (SRC / WATERMARK).exists():
        w = TMP / "watermark.wav"
        to_wav(SRC / WATERMARK, w)
        wm = read_wav(w)
    outro = max(OUTRO_SEC, len(wm) / SR + 1.0) if wm is not None else OUTRO_SEC
    scenes = [("card", None, CARD_SEC, None, None)] + spec["scenes"] + [("outro", None, outro, None, None)]
    starts, t = [], 0.0
    for sc in scenes:                                   # start time of every segment after cross-fades
        starts.append(t)
        t += sc[2] - XF
    total = t + XF

    inputs, chains, cues = [], [], []
    for i, (kind, src, dur, spoken, cap) in enumerate(scenes):
        if kind in ("card", "outro"):
            png = TMP / f"{key}_{kind}.png"
            title = spec["title"] if kind == "card" else "Smart Land"
            sub = spec["subtitle"] if kind == "card" else "حلول تقنية ذكية منذ 2011"
            shot(card_html(title, sub), png)
            inputs += ["-loop", "1", "-t", str(dur), "-i", str(png)]
            chains.append(f"[{i}:v]fps={FPS},format=yuv420p,setsar=1[s{i}]")
        elif kind == "still":                            # slow zoom on a still image (Ken Burns)
            inputs += ["-loop", "1", "-t", str(dur), "-i", str(SRC / src)]
            n = int(dur * FPS)
            chains.append(f"[{i}:v]scale=2560:-2,crop=2560:1440,zoompan=z='min(zoom+0.0007,1.12)':d={n}:"
                          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p,setsar=1[s{i}]")
        else:
            inputs += ["-t", str(dur), "-i", str(SRC / src)]
            chains.append(f"[{i}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[s{i}]")

    # cross-fade chain
    last = "s0"
    for i in range(1, len(scenes)):
        chains.append(f"[{last}][s{i}]xfade=transition=fade:duration={XF}:offset={starts[i]:.3f}[x{i}]")
        last = f"x{i}"

    # voice-over and caption overlays with the same timing
    voice_track = np.zeros(int(total * SR))
    n_in = len(scenes)
    free_at = 0.0                                       # a new sentence never starts before the last one ends
    sentence = 0
    for i, (kind, src, dur, spoken, cap) in enumerate(scenes):
        if not spoken:
            continue
        v = recorded(key, sentence) if key in VOICE else voice(spoken, f"{key}_{i}")
        sentence += 1
        a = max(starts[i] + 0.5, free_at + 0.25)
        b = a + len(v) / SR + 0.35
        free_at = b
        voice_track[int(a * SR):int(a * SR) + len(v)] += v
        png = TMP / f"{key}_cap{i}.png"
        shot(caption_html(cap), png, transparent=True)
        inputs += ["-i", str(png)]
        chains.append(f"[{last}][{n_in}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[o{i}]")
        last = f"o{i}"
        n_in += 1
        cues.append((a, b, cap))

    if wm is not None:                                  # sound logo over the closing card
        s = int((starts[-1] + 0.4) * SR)
        voice_track[s:s + len(wm)] += wm[:len(voice_track) - s] * 0.8

    # ambience from the original clips (quiet), music, voice
    amb = np.zeros_like(voice_track)
    for i, (kind, src, dur, *_rest) in enumerate(scenes):
        if kind != "clip":
            continue
        w = TMP / f"{key}_amb{i}.wav"
        to_wav(SRC / src, w, ["-t", str(dur)])
        a = read_wav(w)
        a = a / (np.abs(a).max() + 1e-6)
        fade = np.minimum(1, np.minimum(np.arange(len(a)), np.arange(len(a))[::-1]) / (XF * SR))
        s = int(starts[i] * SR)
        amb[s:s + len(a)] += (a * fade)[:len(amb) - s]
    mus = music(total, seed=len(key))
    talking = np.convolve((np.abs(voice_track) > 0.01).astype(float), np.ones(SR // 4) / (SR // 4), "same")
    duck = 1 - 0.6 * np.clip(talking * 3, 0, 1)                    # music goes down while the voice speaks
    mix = 0.10 * amb + 0.22 * mus * duck + 0.95 * voice_track
    mix = mix / np.abs(mix).max() * 0.89
    wav = TMP / f"{key}_mix.wav"
    write_wav(mix, wav)
    inputs += ["-i", str(wav)]

    mp4 = OUT / f"{key}.mp4"
    graph = ";".join(chains)
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", f"[{last}]", "-map", f"{n_in}:a",
         "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "112k", "-movflags", "+faststart", str(mp4)])

    # poster image (AVIF + WEBP) from the middle of the first clip
    poster = TMP / f"{key}_poster.png"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{starts[1] + 3:.2f}", "-i", str(mp4), "-frames:v", "1", str(poster)])
    run(["cwebp", "-quiet", "-q", "75", str(poster), "-o", str(OUT / f"{key}-poster.webp")])
    run(["avifenc", "-q", "50", "-s", "6", str(poster), str(OUT / f"{key}-poster.avif")])

    with open(OUT / f"{key}.vtt", "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for n, (a, b, cap) in enumerate(cues, 1):
            f.write(f"{n}\n{vtt_time(a)} --> {vtt_time(b)}\n{cap}\n\n")
    size = mp4.stat().st_size / 1e6
    print(f"{key}: {total:.1f}s, {size:.1f} MB, {len(cues)} captions")
    return {"key": key, "seconds": round(total, 1), "mb": round(size, 2), "captions": len(cues)}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    info = [build(k, v) for k, v in VIDEOS.items()]
    (OUT / "videos.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
