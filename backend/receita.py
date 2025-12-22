import os
import json
import re
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import unicodedata

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
    doencas: list[str] = []

# Ingredientes proibidos por doença com substituições
PROIBIDOS = {
    "diabetes": {
        "açúcar": "adoçante natural (eritritol ou xilitol)",
        "açúcar refinado": "adoçante natural (eritritol ou xilitol)",
        "mel": "adoçante natural (eritritol ou xilitol)",
        "chocolate ao leite": "chocolate amargo sem açúcar",
        "refrigerante": "água ou chá sem açúcar",
        "bolo industrializado": "bolo caseiro sem açúcar"
    },
    "hipertensao": {
        "sal": "sal light ou ervas aromáticas",
        "salsicha": "frango ou peru sem sal",
        "presunto": "peito de peru sem sal",
        "queijo processado": "queijo branco magro",
        "molho pronto": "molho caseiro sem sal",
        "conservas": "legumes frescos ou congelados"
    },
    "colesterol": {
        "manteiga": "azeite de oliva",
        "creme de leite": "iogurte natural desnatado",
        "queijo amarelo": "queijo branco magro",
        "gordura animal": "azeite ou óleo vegetal",
        "frituras": "assar ou cozinhar",
        "ovos em excesso": "use apenas 1 ou 2 ovos"
    }
}

def remover_acentos(texto):
    """Remove acentos para comparação mais robusta"""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')

def filtrar_ingredientes(ingredientes: list[dict], doencas: list[str]):
    """Substitui ingredientes proibidos por alternativas saudáveis, mantendo a quantidade"""
    for ing in ingredientes:
        item_original = ing["item"]
        item_lower = remover_acentos(item_original.lower())
        for d in doencas:
            for proibido, substituto in PROIBIDOS[d].items():
                proibido_lower = remover_acentos(proibido.lower())
                # Usa regex para pegar variações
                pattern = re.compile(r"\b" + re.escape(proibido_lower) + r"\b", re.IGNORECASE)
                if pattern.search(item_lower):
                    ing["item"] = f"{substituto} (substituindo {item_original})"
    return ingredientes

def filtrar_modo_preparo(modo: list[str], doencas: list[str]):
    """Substitui menções de ingredientes proibidos no modo de preparo"""
    modo_filtrado = []
    for passo in modo:
        passo_filtrado = passo
        passo_lower = remover_acentos(passo.lower())
        for d in doencas:
            for proibido, substituto in PROIBIDOS[d].items():
                proibido_lower = remover_acentos(proibido.lower())
                pattern = re.compile(r"\b" + re.escape(proibido_lower) + r"\b", re.IGNORECASE)
                passo_filtrado = pattern.sub(substituto, passo_filtrado)
        modo_filtrado.append(passo_filtrado)
    return modo_filtrado

def gerar_receita_gemini(titulo: str, doencas: list[str]):
    # Prompt para a IA
    restricoes = ""
    if doencas:
        restricoes += "Evite totalmente os ingredientes que podem prejudicar as doenças selecionadas.\n"
        restricoes += "Se algum ingrediente estiver nesta lista, substitua por alternativas saudáveis.\n"

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

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    texto = response.text.strip()
    logging.info(f"Texto bruto do Gemini: {texto}")

    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        raise ValueError("Não foi possível extrair JSON válido do modelo")
    
    receita = json.loads(match.group(0))

    # Filtra ingredientes e modo de preparo
    receita["ingredientes"] = filtrar_ingredientes(receita["ingredientes"], doencas)
    receita["modoPreparo"] = filtrar_modo_preparo(receita.get("modoPreparo", []), doencas)
    
    logging.info(f"Receita final filtrada: {receita}")
    return receita

@app.post("/gerar-receita")
async def gerar_receita(dados: ReceitaRequest):
    try:
        receita = gerar_receita_gemini(dados.titulo, dados.doencas)
        return receita
    except Exception as e:
        logging.error(f"Erro ao gerar receita: {e}")
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
