# Transcritor de Áudio e Gerador de Atas

Aplicação web desenvolvida em Streamlit para processamento, transcrição e geração de atas resumidas a partir de arquivos de áudio gravados em eventos, reuniões e palestras.

O pipeline executa três etapas principais:
1. **Redução de ruído:** Pré-processamento e filtragem de ruído estático em blocos de áudio para otimizar consumo de memória.
2. **Transcrição:** Utiliza o motor `faster-whisper` (com quantização `int8` para alta velocidade em CPU), suportando múltiplos idiomas e tamanhos de modelo (do `base` ao `large-v3`), com acompanhamento do progresso percentual real.
3. **Geração de ata:** Síntese automática dos pontos discutidos utilizando o Google Gemini (`gemini-3.5-flash`), com linguagem neutra e foco em decisões, números e tópicos abordados.

---

## Funcionalidades

- Suporte a múltiplos formatos de áudio (`MP3`, `WAV`, `M4A`, `OGG`, `AAC`).
- Opções de idioma para transcrição: Português, Inglês e Espanhol.
- Seleção de modelo Whisper (`base`, `small`, `medium`, `large-v3`).
- Barra de progresso com porcentagem em tempo real durante a transcrição.
- Exportação dos resultados em arquivos `.txt` (transcrição completa) e `.md` (ata estruturada).

---

## Pré-requisitos

- Python 3.10 ou superior.
- Chave de API do Google AI Studio (Gemini).

---

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/engfranciscocamara-tech/Transcritor-de-udio.git
cd Transcritor-de-udio
```

2. Crie e ative um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
# No Windows:
.\venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure a chave de API do Gemini:
Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:
```env
GEMINI_API_KEY=sua_chave_aqui
```
*(Você pode obter sua chave gratuitamente no [Google AI Studio](https://aistudio.google.com/)).*

---

## Como Executar

Inicie a aplicação com o comando:

```bash
streamlit run app.py
```

O navegador abrirá automaticamente no endereço local `http://localhost:8501`.

---

## Estrutura do Projeto

```text
├── app.py               # Interface Streamlit e fluxo da aplicação
├── audio_processor.py   # Conversão de áudio e redução de ruído em chunks
├── transcriber.py       # Integração com faster-whisper e callback de progresso
├── summarizer.py        # Chamada ao Google Gemini para geração da ata
├── requirements.txt     # Dependências Python do projeto
└── README.md            # Documentação de uso
```
