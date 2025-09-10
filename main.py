from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import edge_tts
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI(title="EdgeTTS API (EN only, Jenny)")

# Config simplu
TEMP_DIR = "/tmp/audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Voce unica (fixa)
VOICE = "en-US-JennyNeural"


def gen_timestamp_name(prefix: str = "tts", ext: str = "mp3") -> str:
    """
    Genereaza un nume de fisier bazat pe timestamp UTC, potrivit pentru streaming.
    Exemplu: tts_20250910T142355Z_1a2b3c.mp3
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{short}.{ext}"


def _safe_remove(path: str):
    # Helper simplu pentru stergere
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


@app.get("/health")
async def health():
    return {"status": "healthy", "voice": VOICE}


@app.post("/convert-text")
async def convert_text_to_speech(
    text: str = Form(..., description="Text de convertit in MP3"),
):
    # Validari minime
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Textul nu poate fi gol")

    # Numele fisierului rezultat pentru download (potrivit streamingului)
    download_name = gen_timestamp_name()
    output_path = os.path.join(TEMP_DIR, download_name)

    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_path)

        bg = BackgroundTask(_safe_remove, output_path)
        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename=download_name,
            background=bg,
        )
    except Exception as e:
        _safe_remove(output_path)
        raise HTTPException(status_code=500, detail=f"Eroare la generarea audio: {e}")


@app.post("/convert-file")
async def convert_file_to_speech(
    file: UploadFile = File(..., description="Fisier .txt pentru TTS"),
):
    # Accept doar .txt
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Doar fisiere .txt sunt acceptate")

    try:
        content = await file.read()
        text = content.decode("utf-8").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Fisierul este gol")

        download_name = gen_timestamp_name(prefix=Path(file.filename).stem or "tts")
        output_path = os.path.join(TEMP_DIR, download_name)

        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_path)

        bg = BackgroundTask(_safe_remove, output_path)
        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename=download_name,
            background=bg,
        )
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Fisierul nu este UTF-8 valid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la procesare: {e}")


if __name__ == "__main__":
    import uvicorn
    # ruleaza: uvicorn acest_fisier:app --reload --port 9000
    uvicorn.run(app, host="0.0.0.0", port=9000)
