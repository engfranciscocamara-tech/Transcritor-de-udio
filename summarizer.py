import os
from google import genai
from google.genai import types

def generate_minutes(text: str, api_key: str) -> str:
    """
    Usa o Google Gemini para gerar a ata da transcrição.
    Aplica estritamente as regras de estilo de comunicação natural, 
    sem metáforas ou jargões de IA.
    """
    if not api_key:
        return "Erro: Chave da API do Google não fornecida."
        
    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "Você é um redator profissional especializado em criar atas de reuniões e palestras. "
            "Ao redigir o resumo e a ata do texto fornecido, você DEVE seguir estritamente as seguintes regras: "
            "1. Elimine completamente o uso de clichês de IA, metáforas dramáticas, adjetivações exageradas e jargões robóticos. "
            "2. Nunca utilize expressões grandiosas como 'A dança dos números...', 'O veredito final...', etc. Seja direto. "
            "3. Estão banidos termos absolutos como 'Solução definitiva', 'Em suma...', 'Vale ressaltar que...', 'Por fim, podemos concluir que...'. Vá direto ao ponto. "
            "4. Escreva em tom neutro, objetivo, fluido e focado em fatos. Economize palavras. Relate estatísticas de forma técnica ou jornalística. "
            "5. Estruture a ata em formato Markdown com marcadores claros e seções objetivas."
        )
        
        prompt = (
            "Leia a transcrição abaixo e crie uma ata resumo contendo os principais pontos comentados, "
            "decisões tomadas e fatos relatados.\n\n"
            f"TRANSCRIÇÃO:\n{text}"
        )
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2, # Baixa temperatura para fatos mais diretos e menos "criativos"
            )
        )
        
        return response.text
        
    except Exception as e:
        return f"Erro ao gerar a ata: {str(e)}"
