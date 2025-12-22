import os
import json
import re
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada
class ReceitaRequest(BaseModel):
    titulo: str
    doencas: dict  # { "diabetes": true, "hipertensao": false, "colesterol": true }

# Função para gerar receita via Gemini
def gerar_receita_gemini(titulo: str, doencas: dict):
    # Mapeamento básico de ingredientes proibidos
    proibidos = []
    if doencas.get("diabetes"):
        proibidos += ["açúcar", "mel", "calda de chocolate", "refrigerante"]
    if doencas.get("hipertensao"):
        proibidos += ["sal", "embutidos", "molho pronto", "enlatados"]
    if doencas.get("colesterol"):
        proibidos += ["manteiga", "creme de leite", "frituras", "gema de ovo"]

    proibir_texto = ""
    if proibidos:
        proibir_texto = "NÃO use os seguintes ingredientes: " + ", ".join(proibidos) + "."

    prompt = f"""
Crie uma receita adequada para pessoas com Alzheimer.
{proibir_texto}

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

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    texto = response.text.strip()
    logging.info(f"Texto bruto do Gemini: {texto}")

    # Extrair JSON
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        raise ValueError("Não foi possível extrair JSON válido do modelo")
    
    receita = json.loads(match.group(0))
    logging.info(f"Receita JSON extraída: {receita}")
    return receita

# Endpoint real usando Gemini
@app.post("/gerar-receita")
async def gerar_receita(dados: ReceitaRequest):
    try:
        receita = gerar_receita_gemini(dados.titulo, dados.doencas)
        return receita
    except Exception as e:
        logging.error(f"Erro ao gerar receita com Gemini: {e}")
        # fallback simples
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
