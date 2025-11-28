"""
Test script for the Typhoon Isan ASR API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

def test_transcribe(audio_file_path):
    """Test single file transcription"""
    print(f"Testing transcription with file: {audio_file_path}...")

    with open(audio_file_path, "rb") as f:
        files = {"file": (audio_file_path, f, "audio/wav")}
        response = requests.post(f"{BASE_URL}/transcribe", files=files)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"Transcription: {result.get('text', '')}\n")
    else:
        print(f"Error: {response.text}\n")

def test_batch_transcribe(audio_files):
    """Test batch transcription"""
    print(f"Testing batch transcription with {len(audio_files)} files...")

    files = []
    file_handles = []

    try:
        for audio_file in audio_files:
            f = open(audio_file, "rb")
            file_handles.append(f)
            files.append(("files", (audio_file, f, "audio/wav")))

        response = requests.post(f"{BASE_URL}/transcribe/batch", files=files)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
        else:
            print(f"Error: {response.text}\n")

    finally:
        for f in file_handles:
            f.close()

if __name__ == "__main__":
    # Test health check
    test_health_check()

    # Test single file transcription
    # Replace with your actual WAV file path
    # test_transcribe("path/to/your/audio.wav")

    # Test batch transcription
    # Replace with your actual WAV file paths
    # test_batch_transcribe(["audio1.wav", "audio2.wav"])

    print("Uncomment the test functions and provide WAV file paths to test transcription")
