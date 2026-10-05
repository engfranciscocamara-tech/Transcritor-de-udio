import os
import time
import numpy as np
import soundfile as sf
import noisereduce as nr

def process_audio(file_path: str) -> str:
    """
    Carrega o arquivo de áudio, converte para 16kHz mono (ideal para Whisper)
    e aplica redução de ruído em pedaços (chunks) para economizar memória.
    Retorna o caminho do novo arquivo de áudio processado.
    """
    print(f"Iniciando processamento do áudio: {file_path}")
    start_time = time.time()
    
    # 1. Converter o áudio original para 16kHz mono com ffmpeg (via imageio_ffmpeg)
    import imageio_ffmpeg
    import subprocess
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    temp_wav = "temp_mono.wav"
    
    # Comando ffmpeg para forçar mono (-ac 1) e 16kHz (-ar 16000)
    cmd = [ffmpeg_exe, "-y", "-i", file_path, "-ac", "1", "-ar", "16000", temp_wav]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Ler o áudio como array numpy (usando soundfile)
    y, sr = sf.read(temp_wav)
    
    print(f"Áudio carregado. Duração: {len(y)/sr:.2f} segundos. Iniciando redução de ruído...")
    
    # 4. Aplicar redução de ruído em chunks (pedaços) para evitar estouro de memória
    # Vamos processar em blocos de 5 minutos
    chunk_duration = 5 * 60  # 5 minutos
    chunk_size = chunk_duration * sr
    
    cleaned_y = np.zeros_like(y)
    
    for i in range(0, len(y), chunk_size):
        end = min(i + chunk_size, len(y))
        chunk = y[i:end]
        
        # Obter amostra de ruído do próprio chunk (assumindo que o primeiro segundo do chunk tem ruído de fundo)
        noise_clip = chunk[:sr] if len(chunk) > sr else chunk
        
        # Aplicar noisereduce (stationary)
        reduced_chunk = nr.reduce_noise(y=chunk, sr=sr, y_noise=noise_clip, stationary=True)
        
        cleaned_y[i:end] = reduced_chunk
        print(f"Processado chunk {i//chunk_size + 1}")
    
    # 5. Salvar o arquivo final limpo
    output_path = "cleaned_audio.wav"
    sf.write(output_path, cleaned_y, sr)
    
    # Remover o temp
    if os.path.exists(temp_wav):
        os.remove(temp_wav)
        
    print(f"Processamento concluído em {time.time() - start_time:.2f}s. Arquivo limpo: {output_path}")
    return output_path
