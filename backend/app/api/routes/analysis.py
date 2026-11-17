"""MIDI upload and analysis endpoint."""

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.schemas import AnalysisResponse
from app.api.uploads import read_midi_upload
from app.midi.parser import MidiParseError
from app.services.analysis_service import analyze_midi

router = APIRouter(tags=["analysis"])


@router.post("/analysis", response_model=AnalysisResponse)
async def analyze(file: UploadFile) -> AnalysisResponse:
    data, file_name = await read_midi_upload(file)
    try:
        return await run_in_threadpool(analyze_midi, data, file_name)
    except MidiParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
