"""Classe base per gli agenti. Pattern ispirati a Microsoft ai-agents-for-beginners."""
import json
from typing import List, Dict, Any, Optional, Callable
from src.llm_client import LLMClient
from src.tools import call_tool, list_tools, TOOL_REGISTRY


class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str,
                 llm: Optional[LLMClient] = None, tools: Optional[List[str]] = None,
                 memory: Optional[List[Dict[str, str]]] = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm or LLMClient()
        self.tool_names = tools or []
        self.memory = memory if memory is not None else []

    def _tool_specs(self) -> List[Dict[str, Any]]:
        specs = []
        for n in self.tool_names:
            t = TOOL_REGISTRY.get(n)
            if t:
                specs.append({"name": t["name"], "description": t["description"],
                             "parameters": t["parameters"]})
        return specs

    def _run_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        results = []
        for tc in tool_calls:
            res = call_tool(tc["name"], tc.get("args", {}))
            results.append({"tool": tc["name"], "result": str(res)[:4000]})
        return results

    def think(self, user_input: str, context: Optional[str] = None,
              max_tool_rounds: int = 4, temperature: float = 0.5) -> str:
        """
        Ciclo ReAct: ragiona, chiama tool se necessario, osserva, ripeti.
        Ritorna la risposta finale testuale.
        """
        messages = list(self.memory)
        prompt = user_input
        if context:
            prompt = f"CONTESTO:\n{context}\n\nRICHIESTA:\n{user_input}"
        messages.append({"role": "user", "content": prompt})

        tools = self._tool_specs()
        system = self.system_prompt

        for _ in range(max_tool_rounds):
            out = self.llm.chat_with_tools(messages, tools, system=system, temperature=temperature)
            text = out.get("text", "") or ""
            calls = out.get("tool_calls", [])
            if not calls:
                # risposta finale
                self.memory.append({"role": "user", "content": prompt})
                self.memory.append({"role": "assistant", "content": text})
                return text
            # esegui tool e aggiungi osservazione
            messages.append({"role": "assistant", "content": text or "[tool call]"})
            results = self._run_tools(calls)
            obs = "RISULTATI TOOL:\n" + "\n".join(
                f"- {r['tool']}: {r['result']}" for r in results
            )
            messages.append({"role": "user", "content": obs})

        # se esaurisce i round, chiedi risposta finale senza tool
        final = self.llm.chat(messages, system=system, temperature=temperature)
        self.memory.append({"role": "user", "content": prompt})
        self.memory.append({"role": "assistant", "content": final})
        return final

    def reset_memory(self):
        self.memory = []

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"
