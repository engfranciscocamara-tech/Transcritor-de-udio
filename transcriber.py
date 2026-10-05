import time
from faster_whisper import WhisperModel

def transcribe_audio(file_path: str, model_size: str = "base", language: str = "pt", progress_callback=None) -> str:
    """
    Carrega o modelo Whisper (via faster-whisper) e transcreve o arquivo de áudio.
    Permite passar uma função progress_callback(percentage) para rastrear o progresso real.
    """
    print(f"Carregando modelo faster-whisper ({model_size})...")
    # Usa int8 na CPU para ser bem mais rápido e economizar RAM
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"Iniciando transcrição (Idioma: {language})...")
    start_time = time.time()
    
    # Executa a transcrição gerando um iterador de segmentos
    segments, info = model.transcribe(file_path, language=language, beam_size=5)
    
    total_duration = info.duration
    text_chunks = []
    
    for segment in segments:
        text_chunks.append(segment.text)
        
        # O faster-whisper processa em tempo real. 'segment.end' diz em qual segundo do áudio ele está.
        if progress_callback and total_duration > 0:
            percentage = min(100, int((segment.end / total_duration) * 100))
            progress_callback(percentage)
    
    text = " ".join(text_chunks)
    
    print(f"Transcrição concluída em {time.time() - start_time:.2f}s.")
    return text.strip()
