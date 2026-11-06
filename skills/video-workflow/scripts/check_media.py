#!/usr/bin/env python3
"""Read-only SDR delivery checks. Requires ffmpeg and ffprobe on PATH."""

import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def tool_path(name):
    path = shutil.which(name)
    if not path:
        raise ValueError(f"Missing dependency on PATH: {name}")
    return path


def run(command):
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace")[-2000:])
    return result.stdout


def audio_signal(ffmpeg, path):
    command = [ffmpeg, "-nostdin", "-v", "error", "-xerror", "-i", str(path),
               "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
               "-f", "s16le", "pipe:1"]
    count, total, squares, minimum, maximum = 0, 0, 0, 32767, -32768
    # File-backed stderr prevents a full error pipe from blocking stdout.
    with tempfile.TemporaryFile() as errors:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors) as process:
            pending = b""
            while True:
                block = process.stdout.read(65536)
                if not block:
                    break
                block = pending + block
                end = len(block) - len(block) % 2
                samples = array.array("h")
                samples.frombytes(block[:end])
                pending = block[end:]
                if sys.byteorder != "little":
                    samples.byteswap()
                if samples:
                    count += len(samples)
                    total += sum(samples)
                    squares += sum(value * value for value in samples)
                    minimum = min(minimum, min(samples))
                    maximum = max(maximum, max(samples))
            if process.wait():
                errors.seek(0)
                raise ValueError(errors.read().decode("utf-8", errors="replace")[-2000:])
    if not count or pending:
        raise ValueError("No complete decoded audio samples")
    mean = total / count
    rms = math.sqrt(max(0, squares / count - mean * mean)) / 32768
    peak = max(abs(minimum - mean), abs(maximum - mean)) / 32768
    rms_dbfs = 20 * math.log10(max(rms, 1e-12))
    peak_dbfs = 20 * math.log10(max(peak, 1e-12))
    if rms_dbfs < -65 or peak_dbfs < -55:
        raise ValueError(f"Silent or extremely quiet audio: RMS {rms_dbfs:.1f} dBFS, peak {peak_dbfs:.1f} dBFS")
    return {"decoded_audio_seconds": round(count / 16000, 3),
            "rms_dbfs": round(rms_dbfs, 2), "peak_dbfs": round(peak_dbfs, 2),
            "non_silent_signal": True, "actual_listening_completed": False}


def check(path, width, height, duration=None, allow_silent=False):
    if not path.is_file():
        raise ValueError("Input media file does not exist")
    ffprobe, ffmpeg = tool_path("ffprobe"), tool_path("ffmpeg")
    initial_hash = digest(path)
    data = json.loads(run([ffprobe, "-v", "error", "-show_streams", "-show_format",
                           "-of", "json", str(path)]))
    streams = data.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"
                  and not item.get("disposition", {}).get("attached_pic")), None)
    if not video:
        raise ValueError("No video stream")
    failures = []
    if (video.get("width"), video.get("height")) != (width, height):
        failures.append(f"Dimensions must be {width}x{height}")
    if video.get("sample_aspect_ratio") != "1:1":
        failures.append("Sample aspect ratio must be 1:1")
    expected = {"color_space": "bt709", "color_transfer": "bt709",
                "color_primaries": "bt709", "color_range": "tv"}
    for key, value in expected.items():
        if video.get(key) != value:
            failures.append(f"{key}: expected {value}, got {video.get(key)}")
    has_audio = any(item.get("codec_type") == "audio" for item in streams)
    if not has_audio and not allow_silent:
        failures.append("No audio stream")
    actual_duration = float(data.get("format", {}).get("duration", 0))
    if not math.isfinite(actual_duration) or actual_duration <= 0:
        failures.append("Invalid media duration")
    if duration is not None and abs(actual_duration - duration) > 0.2:
        failures.append(f"Duration differs from {duration}s by more than 0.2s")
    if failures:
        raise ValueError("; ".join(failures))
    run([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-i", str(path),
         "-map", f"0:{video['index']}", "-map", "0:a:0?", "-f", "null", "-"])
    audio = {"signal_check_skipped": True, "reason": "deliberate silent delivery"} if allow_silent else audio_signal(ffmpeg, path)
    if digest(path) != initial_hash:
        raise ValueError("Input file changed during checking; rerun against a stable export")
    return {"machine_checks_passed": True, "video_sha256": initial_hash,
            "width": width, "height": height, "duration_seconds": actual_duration,
            "color_metadata": expected, "full_decode_passed": True, "audio": audio,
            "human_review_completed": False, "phone_playback_completed": False,
            "platform_verified": False,
            "limitations": "Metadata and decode checks do not prove correct visual tone mapping, speech quality, subtitles or factual accuracy."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--allow-silent", action="store_true", help="Explicitly permit deliberate silent delivery")
    args = parser.parse_args()
    try:
        if args.width <= 0 or args.height <= 0:
            raise ValueError("Width and height must be positive")
        if args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0):
            raise ValueError("Duration must be finite and positive")
        result = check(args.video.resolve(), args.width, args.height, args.duration, args.allow_silent)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"machine_checks_passed": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
