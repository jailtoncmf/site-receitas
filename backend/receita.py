# receita.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json

# Configura Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# CORS para React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de entrada
class ReceitaRequest(BaseModel):
    titulo: str

# Função para gerar receita via Gemini
def gerar_receita_gemini(titulo: str):
    prompt = f"""
Crie uma receita adequada para pessoas com Alzheimer.

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

    # Garantia de JSON válido
    receita = json.loads(texto)
    return receita

# Endpoint real usando Gemini
@app.post("/gerar-receita")
async def gerar_receita(dados: ReceitaRequest):
    try:
        receita = gerar_receita_gemini(dados.titulo)
        return receita
    except Exception as e:
        # fallback em caso de erro (ex: limite da API)
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
