# API Usage Examples

## Prerequisites

1. Start the server:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

## Example 1: Health Check

Check if the server is running:

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "status": "running",
  "available_models": [
    "typhoon-isan-asr-whisper",
    "monsoon-whisper-medium-gigaspeech2"
  ],
  "loaded_models": [],
  "device": "cpu"
}
```

## Example 2: List Available Models

```bash
curl http://localhost:8000/models
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
      "loaded": false
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

## Example 3: Transcribe Audio (Default Model)

Using the default model `typhoon-isan-asr-whisper`:

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -F "file=@audio.wav"
```

**Response:**
```json
{
  "text": "สวัสดีครับ ยินดีต้อนรับ",
  "model": "typhoon-isan-asr-whisper",
  "language": "th-isan",
  "confidence": null,
  "status": "success"
}
```

## Example 4: Transcribe with Specific Model

### Using Monsoon Whisper for Standard Thai

```bash
curl -X POST "http://localhost:8000/transcribe?model=monsoon-whisper-medium-gigaspeech2" \
  -H "accept: application/json" \
  -F "file=@audio.wav"
```

**Note:** Only Whisper-based models are supported. Real-time models (`typhoon-asr-realtime`, `typhoon-isan-asr-realtime`) require the `typhoon-asr` package separately.

## Example 5: Batch Transcription

Transcribe multiple files at once:

```bash
curl -X POST "http://localhost:8000/transcribe/batch" \
  -H "accept: application/json" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "files=@audio3.wav"
```

**Response:**
```json
{
  "results": [
    {
      "filename": "audio1.wav",
      "text": "สวัสดีครับ",
      "model": "typhoon-isan-asr-whisper",
      "language": "th-isan",
      "status": "success"
    },
    {
      "filename": "audio2.wav",
      "text": "ขอบคุณมาก",
      "model": "typhoon-isan-asr-whisper",
      "language": "th-isan",
      "status": "success"
    },
    {
      "filename": "audio3.wav",
      "text": "ลาก่อน",
      "model": "typhoon-isan-asr-whisper",
      "language": "th-isan",
      "status": "success"
    }
  ],
  "total": 3,
  "model": "typhoon-isan-asr-whisper",
  "status": "completed"
}
```

## Example 6: Batch with Specific Model

```bash
curl -X POST "http://localhost:8000/transcribe/batch?model=monsoon-whisper-medium-gigaspeech2" \
  -H "accept: application/json" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav"
```

## Example 7: Pretty Print JSON Response

Add `| jq` to format the output nicely (requires jq to be installed):

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -F "file=@audio.wav" | jq
```

## Example 8: Save Response to File

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -F "file=@audio.wav" \
  -o response.json
```

## Example 9: Using Windows PowerShell

For Windows users using PowerShell:

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

# Transcribe single file
$file = Get-Item "audio.wav"
$form = @{
    file = $file
}
Invoke-RestMethod -Uri "http://localhost:8000/transcribe" -Method Post -Form $form

# Transcribe with specific model
Invoke-RestMethod -Uri "http://localhost:8000/transcribe?model=monsoon-whisper-medium-gigaspeech2" -Method Post -Form $form
```

## Example 10: Python Requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/")
print(response.json())

# Transcribe single file
url = "http://localhost:8000/transcribe"
files = {"file": open("audio.wav", "rb")}
response = requests.post(url, files=files)
print(response.json())

# Transcribe with specific model (standard Thai)
params = {"model": "monsoon-whisper-medium-gigaspeech2"}
response = requests.post(url, files=files, params=params)
print(response.json())

# Batch transcription
url = "http://localhost:8000/transcribe/batch"
files = [
    ("files", open("audio1.wav", "rb")),
    ("files", open("audio2.wav", "rb")),
    ("files", open("audio3.wav", "rb"))
]
response = requests.post(url, files=files)
print(response.json())
```

## Example 11: Error Handling

### Invalid file format
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "detail": "Only WAV files are supported. Please upload a .wav file."
}
```

## Testing with Sample Audio

If you don't have a WAV file, you can create a simple test file using:

**Linux/Mac:**
```bash
ffmpeg -f lavfi -i "sine=frequency=1000:duration=1" test.wav
```

**Or use an online text-to-speech service to generate a Thai/Isan audio file.**

## Interactive API Documentation

Once the server is running, visit these URLs in your browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can test all endpoints directly from your browser.
