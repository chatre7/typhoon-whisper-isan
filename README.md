# Typhoon ASR API

FastAPI application for transcribing Thai and Isan dialect audio using multiple Typhoon ASR models.

## Features

- **Multiple Model Support**: Choose from 3 different ASR models
- Upload WAV files for transcription
- Batch processing support
- JSON response format
- On-demand model loading with caching
- GPU acceleration support (if available)

## Installation

### Option 1: Docker (Recommended)

The easiest way to run the application:

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The API will be available at `http://localhost:8000`

**Or using Docker directly:**
```bash
# Build the image
docker build -t typhoon-asr-api .

# Run the container
docker run -d -p 8000:8000 --name typhoon-asr typhoon-asr-api

# View logs
docker logs -f typhoon-asr

# Stop and remove
docker stop typhoon-asr && docker rm typhoon-asr
```

### Option 2: Local Installation with uv

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. Install uv (if not already installed):
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Sync dependencies:
```bash
uv sync
```

3. Run the server:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Available Models

| Model | Description | Language | Parameters |
|-------|-------------|----------|------------|
| `typhoon-isan-asr-whisper` | Whisper model for Isan dialect (CER: 8.85%) | Isan dialect | 769M |
| `monsoon-whisper-medium-gigaspeech2` | Whisper model for standard Thai | Thai | 0.8B |

**Note:** The real-time models (`typhoon-asr-realtime`, `typhoon-isan-asr-realtime`) use a different architecture (FastConformer-Transducer) and require the `typhoon-asr` package instead of transformers. They are not included in this API.

## API Endpoints

### 1. Health Check
```
GET /
```

**Response:**
```json
{
  "status": "running",
  "available_models": [
    "typhoon-isan-asr-whisper",
    "monsoon-whisper-medium-gigaspeech2"
  ],
  "loaded_models": ["typhoon-isan-asr-whisper"],
  "device": "cuda"
}
```

### 2. List Available Models
```
GET /models
```

**Response:**
```json
{
  "models": [
    {
      "name": "typhoon-isan-asr-whisper",
      "repo": "scb10x/typhoon-isan-asr-whisper",
      "description": "Whisper model optimized for Isan dialect (highest accuracy, CER: 8.85%)",
      "language": "th-isan",
      "loaded": true
    },
    {
      "name": "monsoon-whisper-medium-gigaspeech2",
      "repo": "scb10x/monsoon-whisper-medium-gigaspeech2",
      "description": "Whisper model for standard Thai language (0.8B parameters)",
      "language": "th",
      "loaded": false
    }
  ]
}
```

### 3. Transcribe Single Audio File
```
POST /transcribe
```

**Parameters:**
- `file`: WAV audio file (multipart/form-data)
- `model`: Model to use (optional, default: `typhoon-isan-asr-whisper`)
  - `typhoon-isan-asr-whisper` - Isan dialect
  - `monsoon-whisper-medium-gigaspeech2` - Standard Thai

**Example using curl (default model):**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav"
```

**Example using curl (specify model):**
```bash
curl -X POST "http://localhost:8000/transcribe?model=monsoon-whisper-medium-gigaspeech2" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/transcribe"
files = {"file": open("audio.wav", "rb")}
params = {"model": "typhoon-isan-asr-whisper"}  # Optional
response = requests.post(url, files=files, params=params)
print(response.json())
```

**Response:**
```json
{
  "text": "ສະບາຍດີ ຊື່ ຫຍັງ",
  "model": "typhoon-isan-asr-whisper",
  "language": "th-isan",
  "confidence": null,
  "status": "success"
}
```

### 4. Batch Transcription
```
POST /transcribe/batch
```

**Parameters:**
- `files`: Multiple WAV audio files (multipart/form-data)
- `model`: Model to use (optional, default: `typhoon-isan-asr-whisper`)

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/transcribe/batch?model=monsoon-whisper-medium-gigaspeech2" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/transcribe/batch"
files = [
    ("files", open("audio1.wav", "rb")),
    ("files", open("audio2.wav", "rb"))
]
params = {"model": "typhoon-isan-asr-whisper"}  # Optional
response = requests.post(url, files=files, params=params)
print(response.json())
```

**Response:**
```json
{
  "results": [
    {
      "filename": "audio1.wav",
      "text": "ສະບາຍດີ",
      "model": "typhoon-isan-asr-whisper",
      "language": "th-isan",
      "status": "success"
    },
    {
      "filename": "audio2.wav",
      "text": "ຂອບໃຈ",
      "model": "typhoon-isan-asr-whisper",
      "language": "th-isan",
      "status": "success"
    }
  ],
  "total": 2,
  "model": "typhoon-isan-asr-whisper",
  "status": "completed"
}
```

## Interactive API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Gradio UI: `http://localhost:8000/ui` (upload a WAV file, pick a model, and transcribe directly from the browser)

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Successful transcription
- `400`: Invalid file format
- `500`: Server error during transcription
- `503`: Model not loaded

**Error Response Example:**
```json
{
  "status": "error",
  "message": "Only WAV files are supported",
  "detail": "Please upload a .wav file."
}
```

## Requirements

### Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+ (optional)
- 4GB+ RAM
- 10GB+ disk space (for models)

### Local Deployment
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- CUDA-capable GPU (optional, for faster processing)
- Sufficient RAM (at least 4GB recommended)

## Model Information

All models are from SCB 10X:

- **typhoon-isan-asr-whisper**: 769M parameters, CER 8.85%, Whisper-based, Apache 2.0 license, best accuracy for Isan dialect
- **monsoon-whisper-medium-gigaspeech2**: 0.8B parameters, Whisper-based, Apache 2.0 license, for standard Thai

### Real-time Models (Not Supported in This API)

The following models require the `typhoon-asr` package and use FastConformer-Transducer architecture:
- `typhoon-asr-realtime`: 114M parameters, CER 9.84%, for standard Thai
- `typhoon-isan-asr-realtime`: 114M parameters, CER 10.65%, for Isan dialect

To use these models, install `pip install typhoon-asr` and use their CLI or Python API instead.

## Notes

- Models are loaded on-demand (lazy loading) when first requested
- Loaded models are cached in memory for subsequent requests
- GPU acceleration is automatically used if CUDA is available
- Temporary files are automatically cleaned up after processing
- You can check which models are loaded using the `/models` endpoint
- Docker: Models are cached in a volume to avoid re-downloading on container restart

## Docker GPU Support

To use GPU acceleration with Docker, uncomment the GPU section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**Prerequisites:**
- NVIDIA GPU with CUDA support
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed

Then rebuild and restart:
```bash
docker-compose down
docker-compose up -d --build
```
