import React, { useState } from "react";
import { Brain, ChefHat, Plus, Trash2 } from "lucide-react";

export default function App() {
  const [titulo, setTitulo] = useState("");
  const [receita, setReceita] = useState(null);
  const [loading, setLoading] = useState(false);

  // Estado das doenças
  const [diabetes, setDiabetes] = useState(false);
  const [hipertensao, setHipertensao] = useState(false);
  const [colesterol, setColesterol] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const gerarReceita = async () => {
    if (!titulo.trim()) {
      alert("Digite um título");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/gerar-receita`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          titulo,
          doencas: {
            diabetes,
            hipertensao,
            colesterol
          }
        }),
      });

      if (!response.ok) throw new Error("Erro no backend");

      const data = await response.json();
      setReceita(data);
    } catch (e) {
      console.error(e);
      alert("Erro ao gerar receita");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`
        * { box-sizing: border-box; font-family: Arial, Helvetica, sans-serif; }
        body { margin: 0; background: #f4f6f8; }
        .container { max-width: 900px; margin: 40px auto; padding: 20px; }
        .card { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); margin-bottom: 24px; }
        h1 { text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #555; margin-bottom: 20px; }
        .icons { display: flex; justify-content: center; gap: 12px; margin-bottom: 10px; }
        input[type=text] { width: 100%; padding: 14px; font-size: 16px; border-radius: 8px; border: 1px solid #ccc; }
        button { margin-top: 12px; width: 100%; padding: 14px; font-size: 16px; border: none; border-radius: 8px; background: #4f46e5; color: white; cursor: pointer; }
        button:disabled { background: #999; }
        .header-receita { display: flex; justify-content: space-between; align-items: start; }
        .section-title { margin-top: 24px; margin-bottom: 8px; font-size: 20px; border-left: 4px solid #4f46e5; padding-left: 8px; }
        ul { padding-left: 20px; }
        li { margin-bottom: 6px; }
        .badge { background: #eef2ff; padding: 8px 12px; border-radius: 6px; display: inline-block; margin-right: 10px; }
        .trash { cursor: pointer; color: #dc2626; }
        .checkbox-group { display: flex; gap: 20px; margin-top: 12px; margin-bottom: 12px; }
      `}</style>

      <div className="container">
        <div className="icons">
          <Brain size={36} color="#4f46e5" />
          <ChefHat size={36} color="#4f46e5" />
        </div>

        <h1>Receitas para Alzheimer</h1>
        <p className="subtitle">
          Receitas simples e nutritivas para a saúde do cérebro
        </p>

        <div className="card">
          <input
            placeholder="Ex: Bolo de Laranja"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && gerarReceita()}
          />

          <p style={{ marginTop: "12px", fontWeight: "bold" }}>
            Você possui alguma dessas doenças?
          </p>

          <div className="checkbox-group">
            <label>
              <input type="checkbox" checked={diabetes} onChange={() => setDiabetes(!diabetes)} /> Diabetes
            </label>
            <label>
              <input type="checkbox" checked={hipertensao} onChange={() => setHipertensao(!hipertensao)} /> Hipertensão
            </label>
            <label>
              <input type="checkbox" checked={colesterol} onChange={() => setColesterol(!colesterol)} /> Colesterol Alto
            </label>
          </div>

          <button onClick={gerarReceita} disabled={loading}>
            {loading ? "Gerando..." : "Gerar Receita"} <Plus size={16} />
          </button>
        </div>

        {receita && (
          <div className="card">
            <div className="header-receita">
              <div>
                <h2>{receita.nome}</h2>
                <p>{receita.descricao}</p>
              </div>
              <Trash2 className="trash" onClick={() => setReceita(null)} />
            </div>

            <div>
              <span className="badge">🍽 {receita.rendimento}</span>
              <span className="badge">⏱ {receita.tempoPreparo}</span>
            </div>

            <h3 className="section-title">Ingredientes</h3>
            <ul>
              {receita.ingredientes.map((i, idx) => (
                <li key={idx}>
                  <strong>{i.quantidade}</strong> de {i.item}
                </li>
              ))}
            </ul>

            <h3 className="section-title">Modo de Preparo</h3>
            <ol>
              {receita.modoPreparo.map((p, idx) => (
                <li key={idx}>{p}</li>
              ))}
            </ol>

            <h3 className="section-title">Benefícios</h3>
            <ul>
              {receita.beneficios.map((b, idx) => (
                <li key={idx}>✅ {b}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </>
  );
}
