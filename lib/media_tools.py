"""Locate the system or pip-bundled FFmpeg without requiring a PATH change."""
import shutil


def ffmpeg_binary():
    executable = shutil.which('ffmpeg')
    if executable:
        return executable
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError('Install requirements-media.txt to provide FFmpeg') from None
