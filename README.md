# 🤖 Mio Agente AI — Sistema Multi-Agente Intelligente (Cloud)

Un sistema **multi-agente** ispirato a Claude (Anthropic) e agli agenti AI moderni.
Tutto nel cloud, nulla sul tuo computer.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aertical17-byte/mio-agente-ai/blob/main/notebooks/demo.ipynb)

## ✨ Caratteristiche

- **Multi-agente**: Planner, Researcher, Coder, Reviewer, Coordinator.
- **Pattern**: pipeline sequenziale, fan-out parallelo, handoff, review loop (metacognizione).
- **Tool use**: calcolatrice, ricerca web, esecuzione Python, file I/O.
- **Memoria**: conversazionale short-term + persistenza.
- **Pluggable LLM**: Anthropic Claude (consigliato per intelligenza), OpenAI, Groq (gratis), Gemini (gratis), OpenRouter, HuggingFace, Ollama.
- **Cloud-only**: GitHub Actions / Colab. Niente sul tuo PC.

## 🧠 Come diventa "intelligente come Claude"

L'intelligenza viene dal modello LLM che colleghi. Per il massimo, usa **Anthropic Claude**:
imposta `ANTHROPIC_API_KEY` (GitHub Secret o Colab secret). Il sistema di orchestrazione
(planning, tool use, memoria, revisione) è il nostro contributo.

## 🚀 Uso rapido (cloud)

### GitHub Actions
1. Vai su **Actions → Run Agent (cloud) → Run workflow**.
2. Inserisci il task e (opzionale) il provider.
3. Il risultato viene salvato come artifact e stampato nei log.

### Google Colab
Clicca il badge sopra e segui il notebook.

### Locale (opzionale, solo se vuoi)
```bash
pip install -r requirements.txt
cp .env.example .env  # inserisci una chiave
python main.py "Spiega i vantaggi del cloud computing" --mode pipeline
python main.py --interactive
```

## 🏗️ Architettura

```
src/
├── llm_client.py        # client LLM unificato (multi-provider)
├── orchestrator.py      # multi-agente: pipeline/parallel/handoff/review
├── memory.py            # memoria conversazionale
├── tools.py             # tool (ispirati a Microsoft)
└── agents/
    ├── base.py          # agente base (ReAct + tool loop)
    ├── planner.py       # pianificazione
    ├── researcher.py    # ricerca
    ├── coder.py         # codice
    ├── reviewer.py      # revisione
    └── coordinator.py   # coordinamento
```

## 📜 Crediti
Vedi [CREDITS.md](CREDITS.md). Pattern multi-agente e tool use ispirati a
[Microsoft ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) (MIT).
Concetti da IBM, Anthropic/Claude, AWS, BCG, MIT Sloan.

## 📄 Licenza
MIT.
