"""Agente coder: scrive ed esegue codice."""
from src.agents.base import BaseAgent

CODER_PROMPT = """Sei il PROGRAMMATORE di un sistema multi-agente intelligente.
Il tuo compito: scrivere codice pulito, funzionante e ben commentato per risolvere il task.

Usa i tool: run_python (per testare), write_file, read_file.
Restituisci il codice completo e spiegane il funzionamento.
Se un test fallisce, correggi e riprova (metacognizione)."""


class CoderAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(
            name="Coder",
            role="programmazione",
            system_prompt=CODER_PROMPT,
            llm=llm,
            tools=["run_python", "write_file", "read_file", "list_directory", "calculator"],
        )
