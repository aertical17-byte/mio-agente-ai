"""Agente reviewer: critica e migliora il lavoro degli altri agenti."""
from src.agents.base import BaseAgent

REVIEWER_PROMPT = """Sei il REVISORE di un sistema multi-agente intelligente.
Il tuo compito: valutare criticamente il lavoro prodotto dagli altri agenti.

Controlla: correttezza, completezza, qualita', sicurezza, coerenza con la richiesta.
Restituisci: punti di forza, problemi trovati (con severita'), suggerimenti di miglioramento, verdetto (APPROVATO / DA RIVEDERE).
Sii rigoroso ma costruttivo."""


class ReviewerAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(
            name="Reviewer",
            role="revisione",
            system_prompt=REVIEWER_PROMPT,
            llm=llm,
            tools=["calculator"],
        )
