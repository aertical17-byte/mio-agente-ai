"""Agente pianificatore: decompone un task in passi."""
from src.agents.base import BaseAgent

PLANNER_PROMPT = """Sei il PIANIFICATORE di un sistema multi-agente intelligente.
Il tuo compito: analizzare la richiesta dell'utente e produrre un piano d'azione chiaro e strutturato.

Output richiesto (in italiano):
1. Obiettivo finale.
2. Passi numerati (3-7), ognuno con: azione, agente responsabile (ricercatore/coder/reviewer), output atteso.
3. Criteri di successo.

Sii conciso ma completo. Non eseguire tu il lavoro: pianifica per gli altri agenti."""


class PlannerAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(
            name="Planner",
            role="pianificazione",
            system_prompt=PLANNER_PROMPT,
            llm=llm,
            tools=[],
        )
