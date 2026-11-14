"""Procedural 2D stickman horror animation for LAST PERSON.

The renderer creates original frame-by-frame artwork with Pillow and encodes it
through FFmpeg. It uses no image-generation API, 3D engine, or external art.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH = 720
HEIGHT = 1280
FPS = 12
BG_TOP = (10, 12, 20)
BG_BOTTOM = (29, 24, 35)
INK = (225, 225, 230)
ACCENT = (166, 38, 48)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _line(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], fill=INK, width=9):
    draw.line(points, fill=fill, width=width, joint="curve")


def _stickman(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float,
              phase: float, scared: bool = False, shadow: bool = False):
    color = (18, 17, 24) if shadow else INK
    w = max(4, int(9 * scale))
    bob = math.sin(phase * 2) * 9 * scale
    head_r = 38 * scale
    hx, hy = x, y - 190 * scale + bob
    draw.ellipse((hx-head_r, hy-head_r, hx+head_r, hy+head_r),
                 outline=color, width=w)
    neck = (x, y - 150 * scale + bob)
    shoulder = (x, y - 130 * scale + bob)
    hip = (x + math.sin(phase) * 8 * scale, y - 48 * scale)
    _line(draw, [neck, shoulder, hip], color, w)
    arm_swing = math.sin(phase * 2.4) * 34 * scale
    if scared:
        _line(draw, [shoulder, (x-42*scale, y-165*scale), (x-65*scale, y-205*scale)], color, w)
        _line(draw, [shoulder, (x+42*scale, y-165*scale), (x+65*scale, y-205*scale)], color, w)
    else:
        _line(draw, [shoulder, (x-48*scale, y-92*scale+arm_swing), (x-55*scale, y-48*scale+arm_swing)], color, w)
        _line(draw, [shoulder, (x+48*scale, y-92*scale-arm_swing), (x+55*scale, y-48*scale-arm_swing)], color, w)
    stride = math.sin(phase * 2.4) * 38 * scale
    _line(draw, [hip, (x-30*scale-stride, y+12*scale), (x-36*scale-stride, y+78*scale)], color, w)
    _line(draw, [hip, (x+30*scale+stride, y+12*scale), (x+36*scale+stride, y+78*scale)], color, w)
    if scared and not shadow:
        draw.ellipse((x-12*scale, hy-8*scale, x-3*scale, hy+3*scale), fill=ACCENT)
        draw.ellipse((x+5*scale, hy-8*scale, x+14*scale, hy+3*scale), fill=ACCENT)


def _background(draw: ImageDraw.ImageDraw, prompt: str, beat: int, progress: float):
    p = prompt.lower()
    if any(k in p for k in ("forest", "woods", "tree", "camp")):
        ground = 950
        for i in range(9):
            tx = (i * 103 + 35) % WIDTH
            draw.rectangle((tx-15, 250, tx+15, ground), fill=(15, 19, 23))
            draw.ellipse((tx-100, 120, tx+100, 510), fill=(17, 25, 27))
    elif any(k in p for k in ("school", "classroom", "library")):
        ground = 1000
        for x in (100, 300, 500, 680):
            draw.rectangle((x-35, 500, x+35, 850), outline=(65, 62, 73), width=8)
            draw.line((x-35, 610, x+35, 610), fill=(65, 62, 73), width=5)
    else:
        ground = 1030
        # Door and window give a recognisable interior without external artwork.
        draw.rectangle((475, 370, 650, ground), outline=(88, 76, 82), width=12)
        draw.ellipse((615, 690, 635, 710), fill=(170, 133, 83))
        draw.rectangle((75, 330, 270, 560), outline=(68, 78, 94), width=10)
        draw.line((172, 335, 172, 555), fill=(68, 78, 94), width=6)
        draw.line((80, 445, 265, 445), fill=(68, 78, 94), width=6)
    draw.rectangle((0, ground, WIDTH, HEIGHT), fill=(17, 16, 23))
    draw.line((0, ground, WIDTH, ground), fill=(76, 62, 70), width=5)
    # A soft red light grows during the beat.
    glow = int(18 + 30 * progress)
    draw.ellipse((WIDTH-210, 430, WIDTH+100, 900), fill=(glow, 12, 22))


def _frame(prompt: str, beat: int, frame_index: int, frames_in_beat: int) -> Image.Image:
    progress = frame_index / max(1, frames_in_beat - 1)
    phase = frame_index / FPS + beat * 0.8
    image = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
    d = ImageDraw.Draw(image)
    # Draw a vertical gradient by horizontal bands; avoids per-pixel Python loops.
    for yy in range(0, HEIGHT, 8):
        t = yy / HEIGHT
        c = tuple(int(_lerp(BG_TOP[i], BG_BOTTOM[i], t)) for i in range(3))
        d.rectangle((0, yy, WIDTH, min(HEIGHT, yy + 8)), fill=c)
    _background(d, prompt, beat, progress)
    # Slow camera drift and a character that subtly walks, turns, and recoils.
    base_x = WIDTH * (0.42 + 0.08 * math.sin(beat * 1.4))
    x = base_x + math.sin(progress * math.pi * 2 + beat) * 42
    scale = 1.18 + 0.08 * math.sin(progress * math.pi)
    scared = beat >= 3 and progress > 0.45
    _stickman(d, x, 950, scale, phase, scared=scared)
    # A second, looming silhouette gradually appears in later beats.
    if beat >= 2:
        reveal = max(0.0, min(1.0, (progress + (beat - 2) * 0.24) * 1.4))
        if reveal:
            sx = 565 - progress * 85
            _stickman(d, sx, 990, 1.38 * reveal, phase * 0.35,
                      shadow=True)
    # Film grain specks are deterministic and cheap.
    for i in range(55):
        gx = (i * 131 + frame_index * 17) % WIDTH
        gy = (i * 197 + frame_index * 29) % HEIGHT
        d.point((gx, gy), fill=(40, 38, 47))
    return image


def render_stickman_horror(scene_prompts: list[str], duration: float,
                           audio_path: Path, srt_path: Path, out_path: Path) -> None:
    if not scene_prompts:
        raise ValueError("No scene prompts supplied for stickman animation")
    if duration < 55 or duration > 95:
        raise ValueError(f"Voiceover is {duration:.1f}s; LAST PERSON target is 60-90s. Regenerate the narration.")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    silent_path = out_path.with_name("animation_silent.mp4")
    total_frames = int(math.ceil(duration * FPS))
    beat_count = len(scene_prompts)
    frames_per_beat = math.ceil(total_frames / beat_count)

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-pix_fmt", "yuv420p", str(silent_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        assert proc.stdin is not None
        for frame_no in range(total_frames):
            beat = min(beat_count - 1, frame_no // frames_per_beat)
            local = frame_no - beat * frames_per_beat
            frame = _frame(scene_prompts[beat], beat, local, frames_per_beat)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        code = proc.wait()
        if code:
            raise RuntimeError(f"FFmpeg animation encoding failed with exit code {code}")
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise

    subtitle_path = Path(srt_path).resolve()
    audio_path = Path(audio_path).resolve()
    ambience_path = out_path.with_name("horror_ambience.wav")
    # Original, procedurally generated ambient drone; no copyrighted music or API.
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"sine=frequency=48:sample_rate=44100:duration={duration:.3f}",
        "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.035:sample_rate=44100:duration={duration:.3f}",
        "-filter_complex",
        "[0:a]volume=0.22[tone];[1:a]lowpass=f=420,volume=0.28[air];"
        "[tone][air]amix=inputs=2:duration=longest,afade=t=in:st=0:d=2,"
        f"afade=t=out:st={max(0, duration - 3):.3f}:d=3[bed]",
        "-map", "[bed]", "-c:a", "pcm_s16le", str(ambience_path),
    ], check=True)
    # Escape characters used by FFmpeg's subtitles filter parser.
    subtitle_arg = str(subtitle_path).replace("\\\\", "/").replace(":", "\\\\:").replace("'", "\\\\'")
    mux = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-i", str(silent_path), "-i", str(audio_path), "-i", str(ambience_path),
        "-filter_complex", "[1:a]volume=1.0[voice];[2:a]volume=0.22[amb];"
        "[voice][amb]amix=inputs=2:duration=first:dropout_transition=2[mixed]",
        "-vf", f"scale=1080:1920:flags=fast_bilinear,subtitles='{subtitle_arg}':force_style='FontName=Arial,FontSize=19,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=145,MarginL=70,MarginR=70'",
        "-map", "0:v:0", "-map", "[mixed]", "-c:v", "libx264", "-preset", "fast",
        "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart", str(out_path.resolve()),
    ]
    subprocess.run(mux, check=True)
    silent_path.unlink(missing_ok=True)
    ambience_path.unlink(missing_ok=True)
