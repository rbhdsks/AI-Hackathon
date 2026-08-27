"""Create a captioned MP4 walkthrough from verified presentation frames."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "tmp" / "presentation"
OUTPUT = ROOT / "output" / "video" / "PatientTriage_AI_Prototype_Walkthrough.mp4"
CONCAT = ROOT / "tmp" / "presentation" / "walkthrough.concat.txt"

SEQUENCE = [
    (1, 5.0),
    (2, 5.5),
    (3, 5.5),
    (4, 5.5),
    (5, 6.0),
    (7, 7.0),
    (6, 6.5),
    (8, 6.5),
    (9, 7.0),
    (10, 6.5),
    (11, 6.5),
    (12, 6.5),
    (13, 7.0),
]


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for slide_number, duration in SEQUENCE:
        frame = (SLIDES / f"slide-{slide_number:02d}.png").resolve()
        if not frame.exists():
            raise FileNotFoundError(frame)
        lines.extend([f"file '{frame}'", f"duration {duration}"])
    final_frame = (SLIDES / f"slide-{SEQUENCE[-1][0]:02d}.png").resolve()
    lines.append(f"file '{final_frame}'")
    CONCAT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(CONCAT),
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-vf",
        (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,"
            "fps=30,format=yuv420p"
        ),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "21",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-shortest",
        "-movflags",
        "+faststart",
        "-metadata",
        "title=PatientTriage.ai Prototype Walkthrough",
        "-metadata",
        "comment=Synthetic prototype only; not for patient care",
        str(OUTPUT),
    ]
    subprocess.run(command, check=True)
    return OUTPUT


if __name__ == "__main__":
    print(build())
