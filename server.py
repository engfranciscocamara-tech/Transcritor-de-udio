import os
import uuid
import shutil
import tempfile
import threading
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from audio_processor import process_audio
from transcriber import transcribe_audio
from summarizer import generate_minutes

# Carregar chave do .env se existir
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app = FastAPI(title="Transcritor de Áudio e Gerador de Atas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Armazenamento em memória do estado das tarefas
jobs: Dict[str, Dict[str, Any]] = {}

@app.get("/")
def get_index():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html não encontrado.")
    return FileResponse(index_path)

def run_transcription_job(job_id: str, temp_input_path: str, model_size: str, language: str):
    clean_audio_path = None
    is_cancelled = lambda: jobs.get(job_id, {}).get("cancelled", False)
    try:
        if is_cancelled():
            raise RuntimeError("Processamento cancelado pelo usuário.")

        # Etapa 1: Limpeza de ruído
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Etapa 1/3: Limpando áudio e reduzindo ruído... [10%]"
        clean_audio_path = process_audio(temp_input_path, is_cancelled=is_cancelled)
        
        if is_cancelled():
            raise RuntimeError("Processamento cancelado pelo usuário.")

        # Etapa 2: Transcrição com faster-whisper
        jobs[job_id]["progress"] = 40
        jobs[job_id]["message"] = f"Etapa 2/3: Transcrevendo com modelo '{model_size}'... [40%]"
        
        def on_progress(p: int):
            actual_p = 40 + int((p / 100.0) * 45)
            jobs[job_id]["progress"] = actual_p
            jobs[job_id]["message"] = f"Etapa 2/3: Transcrevendo com modelo '{model_size}'... [{actual_p}%]"

        transcript = transcribe_audio(
            clean_audio_path,
            model_size=model_size,
            language=language,
            progress_callback=on_progress,
            is_cancelled=is_cancelled
        )

        if is_cancelled():
            raise RuntimeError("Processamento cancelado pelo usuário.")

        if not transcript:
            raise RuntimeError("A transcrição retornou um texto vazio.")

        # Etapa 3: Geração de Ata com Gemini
        jobs[job_id]["progress"] = 90
        jobs[job_id]["message"] = "Etapa 3/3: Gerando ata com a Inteligência Artificial... [90%]"
        minutes = generate_minutes(transcript, GEMINI_API_KEY)

        if is_cancelled():
            raise RuntimeError("Processamento cancelado pelo usuário.")

        # Conclusão
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Processamento concluído com sucesso! [100%]"
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["transcript"] = transcript
        jobs[job_id]["minutes"] = minutes

    except Exception as e:
        if is_cancelled():
            jobs[job_id]["status"] = "cancelled"
            jobs[job_id]["message"] = "Processamento cancelado pelo usuário."
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["message"] = f"Erro no processamento: {str(e)}"
    finally:
        if os.path.exists(temp_input_path):
            try:
                os.remove(temp_input_path)
            except OSError:
                pass
        if clean_audio_path and os.path.exists(clean_audio_path):
            try:
                os.remove(clean_audio_path)
            except OSError:
                pass

@app.post("/api/transcribe")
async def start_transcription(
    file: UploadFile = File(...),
    language: str = Form("pt"),
    model_size: str = Form("large-v3")
):
    job_id = str(uuid.uuid4())
    suffix = os.path.splitext(file.filename or "")[1] or ".mp3"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_input_path = temp_file.name

    jobs[job_id] = {
        "status": "processing",
        "progress": 5,
        "message": "Arquivo recebido. Iniciando processamento... [5%]",
        "transcript": None,
        "minutes": None,
        "error": None,
        "cancelled": False
    }

    thread = threading.Thread(
        target=run_transcription_job,
        args=(job_id, temp_input_path, model_size, language),
        daemon=True
    )
    thread.start()

    return {"job_id": job_id}

@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    jobs[job_id]["cancelled"] = True
    jobs[job_id]["status"] = "cancelled"
    jobs[job_id]["message"] = "Processamento cancelado pelo usuário."
    return {"status": "cancelled", "job_id": job_id}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return jobs[job_id]
