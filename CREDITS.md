# Crediti e fonti

## Pattern e architettura multi-agente
- **Microsoft ai-agents-for-beginners** — https://github.com/microsoft/ai-agents-for-beginners
  - Pattern `@tool` decorator, tipizzazione `Annotated`, `approval_mode`.
  - Pattern `WorkflowBuilder` (add_edge) per pipeline multi-agente sequenziale.
  - Pattern ReAct e tool use.
  - Licenza: MIT. Copyright (c) Microsoft Corporation.
  - Alcune funzioni in `src/tools.py` e `src/orchestrator.py` sono ispirate/adattate da questo repository.

## Concetti e design
- **IBM** — "What are AI agents?" https://www.ibm.com/it-it/think/topics/ai-agents
- **Claude / Anthropic** — https://claude.com/it/solutions/agents
- **AWS** — "What is an AI Agent?" https://aws.amazon.com/it/what-is/ai-agents/
- **BCG** — "AI Agents" https://www.bcg.com/capabilities/artificial-intelligence/ai-agents
- **MIT Sloan** — "Agentic AI explained" https://mitsloan.mit.edu/ideas-made-to-matter/agentic-ai-explained

## Librerie
- anthropic, openai, google-generativeai, groq (SDK provider)
- requests, python-dotenv, pydantic
