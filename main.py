from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from enum import Enum
import torch
from transformers import pipeline
import tempfile
import os
from typing import Optional, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
class ASRModel(str, Enum):
    TYPHOON_ISAN_WHISPER = "typhoon-isan-asr-whisper"
    MONSOON_WHISPER_MEDIUM = "monsoon-whisper-medium-gigaspeech2"

MODEL_CONFIG = {
    ASRModel.TYPHOON_ISAN_WHISPER: {
        "repo": "scb10x/typhoon-isan-asr-whisper",
        "description": "Whisper model optimized for Isan dialect (highest accuracy, CER: 8.85%)",
        "language": "th-isan",
    },
    ASRModel.MONSOON_WHISPER_MEDIUM: {
        "repo": "scb10x/monsoon-whisper-medium-gigaspeech2",
        "description": "Whisper model for standard Thai language (0.8B parameters)",
        "language": "th",
    },
}

# Note: typhoon-asr-realtime and typhoon-isan-asr-realtime require the typhoon-asr package
# and cannot be used with transformers pipeline. They are FastConformer-Transducer models.

app = FastAPI(
    title="Typhoon ASR API",
    description="API for transcribing Thai and Isan dialect audio using Typhoon ASR models",
    version="2.0.0"
)

# Response models
class TranscriptionResponse(BaseModel):
    text: str
    model: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "success"

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None

# Global models cache
loaded_models: Dict[str, any] = {}

def get_or_load_model(model_name: ASRModel):
    """Load a model on-demand or return cached model"""
    global loaded_models

    if model_name not in loaded_models:
        try:
            logger.info(f"Loading model: {model_name}...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

            model_repo = MODEL_CONFIG[model_name]["repo"]
            loaded_models[model_name] = pipeline(
                "automatic-speech-recognition",
                model=model_repo,
                device=0 if device == "cuda" else -1,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                chunk_length_s=30,  # Process audio in 30-second chunks
                return_timestamps=True  # Enable timestamp prediction for long audio
            )
            logger.info(f"Model {model_name} loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load model: {str(e)}"
            )

    return loaded_models[model_name]

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "available_models": [model.value for model in ASRModel],
        "loaded_models": list(loaded_models.keys()),
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.get("/models")
async def list_models():
    """List all available models with descriptions"""
    models_info = []
    for model_enum in ASRModel:
        config = MODEL_CONFIG[model_enum]
        models_info.append({
            "name": model_enum.value,
            "repo": config["repo"],
            "description": config["description"],
            "language": config["language"],
            "loaded": model_enum in loaded_models
        })
    return {"models": models_info}

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="WAV audio file to transcribe"),
    model: ASRModel = Query(
        default=ASRModel.TYPHOON_ISAN_WHISPER,
        description="ASR model to use for transcription"
    )
):
    """
    Transcribe an audio file using specified Typhoon ASR model

    Args:
        file: WAV audio file to transcribe
        model: Model to use (typhoon-isan-asr-whisper, typhoon-isan-asr-realtime, typhoon-asr-realtime)

    Returns:
        JSON response with transcribed text
    """
    # Validate file extension
    if not file.filename.lower().endswith('.wav'):
        raise HTTPException(
            status_code=400,
            detail="Only WAV files are supported. Please upload a .wav file."
        )

    # Load or get cached model
    asr_model = get_or_load_model(model)

    # Create temporary file to store the upload
    temp_file = None
    try:
        # Read file content
        content = await file.read()

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"Processing file: {file.filename} ({len(content)} bytes) with model: {model}")

        # Transcribe the audio
        result = asr_model(temp_file_path)

        # Extract text from result (handle both formats)
        if isinstance(result, dict):
            transcription_text = result.get("text", "")
        elif isinstance(result, str):
            transcription_text = result
        else:
            transcription_text = str(result)

        logger.info(f"Transcription completed: {transcription_text[:100]}...")

        return TranscriptionResponse(
            text=transcription_text,
            model=model.value,
            language=MODEL_CONFIG[model]["language"],
            status="success"
        )

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to transcribe audio: {str(e)}"
        )

    finally:
        # Clean up temporary file
        if temp_file is not None and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {str(e)}")

@app.post("/transcribe/batch")
async def transcribe_batch(
    files: list[UploadFile] = File(..., description="Multiple WAV audio files to transcribe"),
    model: ASRModel = Query(
        default=ASRModel.TYPHOON_ISAN_WHISPER,
        description="ASR model to use for transcription"
    )
):
    """
    Transcribe multiple audio files using specified Typhoon ASR model

    Args:
        files: List of WAV audio files
        model: Model to use (typhoon-isan-asr-whisper, typhoon-isan-asr-realtime, typhoon-asr-realtime)

    Returns:
        JSON response with transcriptions for all files
    """
    # Load or get cached model
    asr_model = get_or_load_model(model)

    results = []

    for file in files:
        try:
            # Validate file extension
            if not file.filename.lower().endswith('.wav'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Only WAV files are supported"
                })
                continue

            # Read and process file
            content = await file.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # Transcribe
            result = asr_model(temp_file_path)

            # Extract text from result (handle both formats)
            if isinstance(result, dict):
                transcription_text = result.get("text", "")
            elif isinstance(result, str):
                transcription_text = result
            else:
                transcription_text = str(result)

            results.append({
                "filename": file.filename,
                "text": transcription_text,
                "model": model.value,
                "language": MODEL_CONFIG[model]["language"],
                "status": "success"
            })

            # Clean up
            os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })

    return {
        "results": results,
        "total": len(files),
        "model": model.value,
        "status": "completed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
