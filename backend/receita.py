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

# Substitutos saudáveis para ingredientes proibidos
SUBSTITUTOS = {
    "açúcar": "adoçante natural (eritritol ou xilitol)",
    "açúcar refinado": "adoçante natural (eritritol ou xilitol)",
    "açúcar demerara": "adoçante natural (eritritol ou xilitol)",
    "açúcar mascavo": "adoçante natural (eritritol ou xilitol)",
    "mel": "adoçante natural (eritritol ou xilitol)",
    "xarope de milho": "adoçante natural (eritritol ou xilitol)",
    "chocolate ao leite": "chocolate 70% cacau ou cacau puro",
    "refrigerante": "suco natural sem açúcar",
    "bolo industrializado": "bolo caseiro com ingredientes naturais",
    "sal": "sal light ou temperos naturais",
    "salsicha": "frango ou peru cozido",
    "presunto": "frango ou peru cozido",
    "queijo processado": "queijo branco ou ricota",
    "molho pronto": "molho caseiro sem sal",
    "conservas": "vegetais frescos",
    "manteiga": "azeite de oliva ou óleo vegetal",
    "creme de leite": "iogurte natural",
    "queijo amarelo": "queijo branco ou ricota",
    "gordura animal": "azeite de oliva",
    "frituras": "assado ou cozido",
    "ovos em excesso": "1 ovo por receita ou claras"
}

# Função para substituir ingredientes proibidos
def filtrar_ingredientes(ingredientes, doencas):
    ingredientes_filtrados = []
    for i in ingredientes:
        nome = i["item"].lower()
        qtd = i["quantidade"]
        substituido = False
        for d in doencas:
            for proibido in PROIBIDOS[d]:
                if proibido in nome:
                    novo = SUBSTITUTOS.get(proibido, proibido)
                    ingredientes_filtrados.append({"item": novo, "quantidade": qtd})
                    substituido = True
                    break
            if substituido:
                break
        if not substituido:
            ingredientes_filtrados.append(i)
    return ingredientes_filtrados

# Função principal que gera receita via Gemini
def gerar_receita_gemini(titulo: str, doencas: list[str]):
    # Cria instrução de restrições com base nas doenças
    restricoes = ""
    if doencas:
        restricoes += "Evite totalmente os seguintes ingredientes:\n"
        for d in doencas:
            restricoes += f"- {', '.join(PROIBIDOS[d])}\n"
        restricoes += "Substitua qualquer ingrediente proibido por alternativas saudáveis.\n"

    # Prompt para Gemini
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

    # Extrai JSON válido
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        raise ValueError("Não foi possível extrair JSON válido do modelo")
    
    receita = json.loads(match.group(0))

    # Filtra ingredientes proibidos
    receita["ingredientes"] = filtrar_ingredientes(receita["ingredientes"], doencas)

    return receita

# Endpoint que recebe título e doenças
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
