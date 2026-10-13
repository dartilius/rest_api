"""Common media rules for playlist forms and REST creation."""

from pathlib import PurePosixPath


def is_audio_file(file):
    suffix = PurePosixPath(file.source.name or "").suffix.lower()
    return file.type == 0 or (file.type == 4 and suffix in {
        ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma", ".opus",
    })
