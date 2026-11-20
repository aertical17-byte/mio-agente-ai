"""Agente ricercatore: raccoglie informazioni (web, memoria)."""
from src.agents.base import BaseAgent

RESEARCHER_PROMPT = """Sei il RICERCATORE di un sistema multi-agente intelligente.
Il tuo compito: raccogliere informazioni accurate e aggiornate per supportare il piano.

Usa i tool disponibili (web_search, read_file) per verificare i fatti.
Restituisci un report strutturato con: fonti, punti chiave, dati numerici, incertezze.
Non inventare dati: se non trovi, dillo esplicitamente."""


class ResearcherAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__(
            name="Researcher",
            role="ricerca",
            system_prompt=RESEARCHER_PROMPT,
            llm=llm,
            tools=["web_search", "read_file", "get_current_datetime"],
        )
