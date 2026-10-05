import os
import streamlit as st
import tempfile
import threading
from audio_processor import process_audio
from transcriber import transcribe_audio
from summarizer import generate_minutes

st.set_page_config(page_title="Transcritor e Gerador de Atas", page_icon="🎙️", layout="wide")

st.title("🎙️ Transcritor e Gerador de Atas")
st.markdown("Faça o upload de um áudio para limpeza de ruído, transcrição de alta qualidade (Whisper) e geração de ata estruturada.")

# Configurações na barra lateral
# Carregar chave do .env ou variável de ambiente
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]

api_key_input = os.getenv("GEMINI_API_KEY", "")

language_options = {
    "Português": "pt",
    "Inglês": "en",
    "Espanhol": "es"
}
selected_lang_name = st.sidebar.selectbox("Idioma do Áudio", list(language_options.keys()))
selected_lang_code = language_options[selected_lang_name]

model_size = st.sidebar.selectbox(
    "Modelo de Transcrição (Whisper)", 
    ["base", "small", "medium", "large-v3"], 
    index=3,
    help="Modelos maiores são mais precisos, mas exigem muito mais tempo e memória. Para máxima qualidade, 'large-v3' é recomendado."
)

uploaded_file = st.file_uploader("Selecione o arquivo de áudio (MP3, WAV, M4A, etc.)", type=["mp3", "wav", "m4a", "ogg", "aac"])

if uploaded_file is not None:
    if st.button("Iniciar Processamento"):
        with st.spinner("Salvando arquivo temporário..."):
            # Salvar arquivo em disco para processamento
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) 
            tfile.write(uploaded_file.read())
            original_path = tfile.name
            tfile.close()

        try:
            progress_bar = st.progress(0, text="Iniciando processamento... [0%]")
            
            # 1. Redução de Ruído
            progress_bar.progress(10, text="Etapa 1/3: Limpando áudio e reduzindo ruído... [10%]")
            clean_audio_path = process_audio(original_path)
            st.success("Áudio limpo com sucesso!")
            
            # 2. Transcrição com barra de progresso real
            progress_bar.progress(40, text=f"Etapa 2/3: Transcrevendo com modelo '{model_size}' (Iniciando... 40%)")
            
            # Função de callback que será chamada pelo faster-whisper com a porcentagem real (0-100)
            def update_progress(p):
                # Vamos mapear a porcentagem da transcrição (0 a 100) para o espaço da barra geral (40 a 85)
                actual_p = 40 + int((p / 100.0) * 45)
                progress_bar.progress(actual_p, text=f"Etapa 2/3: Transcrevendo com modelo '{model_size}' (Processando... {actual_p}%)")
            
            # Transcreve bloqueando a thread principal, mas atualizando a UI via callback
            transcript_text = transcribe_audio(
                clean_audio_path, 
                model_size=model_size, 
                language=selected_lang_code, 
                progress_callback=update_progress
            )
            
            if not transcript_text:
                st.error("A transcrição falhou ou o áudio está vazio.")
                progress_bar.empty()
            else:
                progress_bar.progress(90, text="Etapa 3/3: Gerando ata com a Inteligência Artificial... [90%]")
                st.success("Transcrição concluída!")

                # 3. Geração de Ata
                ata_text = generate_minutes(transcript_text, api_key_input)
                progress_bar.progress(100, text="Processo finalizado! [100%]")
                st.success("Ata gerada com sucesso!")

                # Exibir resultados em colunas
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📝 Transcrição Completa")
                    st.text_area("Texto Transcrito", transcript_text, height=400)
                    st.download_button(
                        label="Baixar Transcrição (.txt)",
                        data=transcript_text,
                        file_name="transcricao.txt",
                        mime="text/plain"
                    )

                with col2:
                    st.subheader("📋 Ata Resumo")
                    st.markdown(ata_text)
                    st.download_button(
                        label="Baixar Ata (.md)",
                        data=ata_text,
                        file_name="ata_resumo.md",
                        mime="text/markdown"
                    )

        except Exception as e:
            st.error(f"Ocorreu um erro durante o processamento: {e}")
            
        finally:
            # Limpeza dos arquivos temporários
            if os.path.exists(original_path):
                os.remove(original_path)
            if 'clean_audio_path' in locals() and os.path.exists(clean_audio_path):
                os.remove(clean_audio_path)
