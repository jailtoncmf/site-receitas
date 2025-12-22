import os
import json
import re
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# Configura Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Permite acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada
class ReceitaRequest(BaseModel):
    titulo: str
    doencas: list[str] = []  # Lista de doenças selecionadas pelo usuário

# Ingredientes proibidos por doença
PROIBIDOS = {
    "diabetes": ["açúcar","açúcar refinado", "açúcar demerara", "açúcar mascavo", "mel", "xarope de milho", "chocolate ao leite", "refrigerante", "bolo industrializado"],
    "hipertensao": ["sal", "salsicha", "presunto", "queijo processado", "molho pronto", "conservas"],
    "colesterol": ["manteiga", "creme de leite", "queijo amarelo", "gordura animal", "frituras", "ovos em excesso"]
}

# Função principal que gera a receita via Gemini
def gerar_receita_gemini(titulo: str, doencas: list[str]):
    # Cria instrução de restrições com base nas doenças
    restricoes = ""
    if doencas:
        restricoes += "Evite totalmente os seguintes ingredientes:\n"
        for d in doencas:
            restricoes += f"- {', '.join(PROIBIDOS[d])}\n"
        restricoes += "Se algum ingrediente estiver nesta lista, substitua por uma alternativa saudável adequada.\n"

    # Prompt completo para a IA
    prompt = f"""
Crie uma receita adequada para pessoas com Alzheimer.
{restricoes}

Responda APENAS com um JSON válido no seguinte formato:

{{
  "nome": "Nome da receita",
  "descricao": "Breve descrição",
  "rendimento": "Ex: 2 porções",
  "tempoPreparo": "Ex: 30 minutos",
  "ingredientes": [
    {{"item": "Ingrediente", "quantidade": "Quantidade"}}
  ],
  "modoPreparo": [
    "Passo 1",
    "Passo 2"
  ],
  "beneficios": [
    "Benefício 1",
    "Benefício 2"
  ]
}}

Título da receita: "{titulo}"
"""

    # Gera conteúdo usando Gemini
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    texto = response.text.strip()
    logging.info(f"Texto bruto do Gemini: {texto}")

    # Extrai JSON válido do texto retornado
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        raise ValueError("Não foi possível extrair JSON válido do modelo")
    
    receita = json.loads(match.group(0))
    logging.info(f"Receita JSON extraída: {receita}")
    return receita

# Endpoint que recebe título e doenças
@app.post("/gerar-receita")
async def gerar_receita(dados: ReceitaRequest):
    try:
        receita = gerar_receita_gemini(dados.titulo, dados.doencas)
        return receita
    except Exception as e:
        logging.error(f"Erro ao gerar receita: {e}")
        # fallback simples caso a IA falhe
        return {
            "nome": f"Receita de {dados.titulo}",
            "descricao": "Receita nutritiva para Alzheimer",
            "rendimento": "2 porções",
            "tempoPreparo": "30 minutos",
            "ingredientes": [
                {"item": "Ingrediente 1", "quantidade": "100g"},
                {"item": "Ingrediente 2", "quantidade": "50g"}
            ],
            "modoPreparo": ["Passo 1", "Passo 2"],
            "beneficios": ["Melhora memória", "Fortalece o cérebro"]
        }
