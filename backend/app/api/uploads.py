"""Shared validation for uploaded MIDI files."""

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

ALLOWED_EXTENSIONS = (".mid", ".midi")


async def read_midi_upload(file: UploadFile) -> tuple[bytes, str]:
    """Returns (content, file name) or raises a 400/413 HTTPException."""
    file_name = file.filename or "upload.mid"
    if not file_name.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only .mid and .midi files are supported.")

    max_bytes = int(get_settings().max_upload_mb * 1024 * 1024)
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File is too large.")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The file is empty.")
    return data, file_name
