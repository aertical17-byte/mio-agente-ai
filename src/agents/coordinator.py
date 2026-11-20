"""Agente coordinatore: smista e orchestra gli altri agenti."""
from src.agents.base import BaseAgent

COORDINATOR_PROMPT = """Sei il COORDINATORE di un sistema multi-agente intelligente.
Il tuo compito: capire la richiesta dell'utente, decidere quali agenti attivare e in che ordine,
e sintetizzare il risultato finale.

Agenti disponibili: Planner, Researcher, Coder, Reviewer.
Rispondi sempre con il risultato finale consolidato, in italiano, chiaro e ben strutturato."""


class CoordinatorAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(
            name="Coordinator",
            role="coordinamento",
            system_prompt=COORDINATOR_PROMPT,
            llm=llm,
            tools=[],
        )
