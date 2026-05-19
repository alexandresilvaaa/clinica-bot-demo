"""
PROJETO 1 — Bot WhatsApp para Clínica com IA
=============================================
Demo funcional para portfólio 99Freelas.
Simula atendimento real: agenda, responde dúvidas, confirma consultas.
"""

from flask import Flask, render_template, request, jsonify
from groq import Groq
from datetime import datetime, timedelta
import os, json, random
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Inicializa Groq de forma segura (não crasha se KEY não estiver setada)
_groq_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=_groq_key) if _groq_key else None

# ── Dados da clínica (simulado) ──────────────────────────────────────────────
CLINICA = {
    "nome": "Clínica Saúde & Bem-Estar",
    "especialidades": ["Clínica Geral", "Pediatria", "Ginecologia", "Dermatologia"],
    "horarios": ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"],
    "telefone": "(11) 99999-0000",
    "endereco": "Rua das Flores, 123 — Centro",
}

# ── Banco de dados simulado ───────────────────────────────────────────────────
conversas = {}   # {telefone: [mensagens]}
agendamentos = [ # dados demo
    {"paciente": "Maria Silva",    "data": "20/05", "hora": "09:00", "medico": "Dr. João",      "status": "confirmado"},
    {"paciente": "Carlos Souza",   "data": "20/05", "hora": "14:00", "medico": "Dra. Ana",      "status": "pendente"},
    {"paciente": "Lucia Ferreira", "data": "21/05", "hora": "10:00", "medico": "Dr. Pedro",     "status": "confirmado"},
    {"paciente": "Roberto Lima",   "data": "21/05", "hora": "15:00", "medico": "Dra. Carla",    "status": "pendente"},
    {"paciente": "Fernanda Costa", "data": "22/05", "hora": "11:00", "medico": "Dr. João",      "status": "confirmado"},
]
estatisticas = {
    "atendimentos_hoje": 47,
    "agendamentos_semana": 183,
    "taxa_confirmacao": "94%",
    "tempo_medio_resposta": "8 segundos",
    "satisfacao": "4.9/5.0",
}

# ── IA do Bot ─────────────────────────────────────────────────────────────────
def responder_bot(telefone, mensagem):
    if not client:
        return "⚠️ IA temporariamente indisponível. Configure GROQ_API_KEY."

    if telefone not in conversas:
        conversas[telefone] = []

    conversas[telefone].append({"role": "user", "content": mensagem})

    historico = conversas[telefone][-8:]

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"""Você é o assistente virtual da {CLINICA['nome']}.
Seja simpático, profissional e objetivo. Responda sempre em português.

INFORMAÇÕES DA CLÍNICA:
- Especialidades: {', '.join(CLINICA['especialidades'])}
- Horários: {', '.join(CLINICA['horarios'])}
- Telefone: {CLINICA['telefone']}
- Endereço: {CLINICA['endereco']}

VOCÊ PODE:
- Agendar consultas (pergunte nome, especialidade e horário preferido)
- Confirmar agendamentos existentes
- Informar sobre especialidades e horários
- Responder dúvidas gerais sobre a clínica

REGRAS:
- Máximo 3 linhas por resposta
- Se precisar de mais info, faça UMA pergunta por vez
- Sempre confirme agendamentos com: ✅ nome, data, horário, especialidade
- Nunca invente informações médicas"""},
            *historico
        ]
    )

    resposta = r.choices[0].message.content
    conversas[telefone].append({"role": "assistant", "content": resposta})
    return resposta

# ── ROTAS ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
        clinica=CLINICA,
        agendamentos=agendamentos,
        stats=estatisticas)

@app.route("/api/mensagem", methods=["POST"])
def mensagem():
    data = request.json
    telefone = data.get("telefone", "demo")
    msg = data.get("mensagem", "")
    if not msg:
        return jsonify({"erro": "mensagem vazia"}), 400
    resposta = responder_bot(telefone, msg)
    hora = datetime.now().strftime("%H:%M")
    return jsonify({"resposta": resposta, "hora": hora})

@app.route("/api/stats")
def stats():
    return jsonify(estatisticas)

@app.route("/api/agendamentos")
def get_agendamentos():
    return jsonify(agendamentos)

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
