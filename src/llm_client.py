"""
Client LLM unificato e pluggable.

Supporta (in ordine di priorita' se piu' chiavi presenti):
  - Anthropic Claude (ANTHROPIC_API_KEY)  -> il piu' "intelligente"
  - OpenAI (OPENAI_API_KEY)
  - Groq (GROQ_API_KEY) - tier gratuito, velocissimo
  - Google Gemini (GEMINI_API_KEY / GOOGLE_API_KEY)
  - OpenRouter (OPENROUTER_API_KEY) - accesso a molti modelli
  - Hugging Face Inference (HF_TOKEN)
  - Ollama locale (OLLAMA_BASE_URL) - opzionale, solo se esplicito

Tutto gira nel cloud: nessun modello viene eseguito sul computer dell'utente
se si usano i provider remoti. Ollama e' opzionale e disabilitato di default.

Crediti: pattern ispirati a Microsoft ai-agents-for-beginners (MIT License).
"""
import os
import json
from typing import Any, Dict, List, Optional, Callable


def _env(*names: str) -> Optional[str]:
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return None


class LLMClient:
    """Wrapper unificato per chiamare diversi provider LLM."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or self._detect_provider()).lower()
        self.model = model or self._default_model(self.provider)
        self._client = self._build_client()

    # ---------- detection ----------
    def _detect_provider(self) -> str:
        if _env("ANTHROPIC_API_KEY"):
            return "anthropic"
        if _env("OPENAI_API_KEY"):
            return "openai"
        if _env("GROQ_API_KEY"):
            return "groq"
        if _env("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            return "gemini"
        if _env("OPENROUTER_API_KEY"):
            return "openrouter"
        if _env("HF_TOKEN", "HUGGINGFACE_TOKEN"):
            return "huggingface"
        if _env("OLLAMA_BASE_URL"):
            return "ollama"
        raise RuntimeError(
            "Nessuna chiave API trovata. Imposta almeno una tra: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, "
            "OPENROUTER_API_KEY, HF_TOKEN. Vedi .env.example"
        )

    def _default_model(self, provider: str) -> str:
        return {
            "anthropic": "claude-sonnet-4-5",
            "openai": "gpt-4o-mini",
            "groq": "llama-3.3-70b-versatile",
            "gemini": "gemini-2.0-flash",
            "openrouter": "anthropic/claude-sonnet-4.5",
            "huggingface": "mistralai/Mistral-7B-Instruct-v0.3",
            "ollama": "llama3.2",
        }.get(provider, "gpt-4o-mini")

    def _build_client(self):
        p = self.provider
        if p == "anthropic":
            import anthropic
            return anthropic.Anthropic(api_key=_env("ANTHROPIC_API_KEY"))
        if p in ("openai", "groq", "openrouter", "gemini"):
            import openai
            base_url = {
                "openai": None,
                "groq": "https://api.groq.com/openai/v1",
                "openrouter": "https://openrouter.ai/api/v1",
                "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
            }[p]
            key = {
                "openai": _env("OPENAI_API_KEY"),
                "groq": _env("GROQ_API_KEY"),
                "openrouter": _env("OPENROUTER_API_KEY"),
                "gemini": _env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            }[p]
            kwargs = {"api_key": key}
            if base_url:
                kwargs["base_url"] = base_url
            return openai.OpenAI(**kwargs)
        if p == "huggingface":
            return None  # usiamo requests diretto
        if p == "ollama":
            import openai
            return openai.OpenAI(
                api_key="ollama",
                base_url=_env("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            )
        raise ValueError(f"Provider sconosciuto: {p}")

    # ---------- chat ----------
    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None,
             temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Chiamata semplice: ritorna testo."""
        p = self.provider
        if p == "anthropic":
            sys_msg = system or ""
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=sys_msg,
                messages=messages,
                temperature=temperature,
            )
            return resp.content[0].text
        if p == "huggingface":
            import requests
            prompt = ""
            if system:
                prompt += f"<s>[INST] {system}\n\n"
            for m in messages:
                prompt += f"{m['role']}: {m['content']}\n"
            prompt += "[/INST]"
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{self.model}",
                headers={"Authorization": f"Bearer {_env('HF_TOKEN','HUGGINGFACE_TOKEN')}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "temperature": temperature}},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "").replace(prompt, "").strip()
            return str(data)
        # OpenAI-compatible
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict],
                        system: Optional[str] = None, temperature: float = 0.4,
                        max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Chat con tool calling nativo (dove supportato) oppure ReAct fallback.
        Ritorna dict: {'text': str, 'tool_calls': [{'name':..., 'args':...}]}
        """
        p = self.provider
        if p == "anthropic":
            return self._anthropic_tools(messages, tools, system, temperature, max_tokens)
        if p in ("openai", "groq", "openrouter", "gemini", "ollama"):
            return self._openai_tools(messages, tools, system, temperature, max_tokens)
        # fallback: ReAct testuale
        return self._react_fallback(messages, tools, system, temperature, max_tokens)

    # ---------- native tool calling ----------
    def _openai_tools(self, messages, tools, system, temperature, max_tokens):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        # converti tools nel formato OpenAI
        oai_tools = []
        for t in tools:
            oai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                },
            })
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=msgs,
            tools=oai_tools if oai_tools else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        msg = resp.choices[0].message
        tool_calls = []
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                tool_calls.append({"id": tc.id, "name": tc.function.name, "args": args})
        return {"text": msg.content or "", "tool_calls": tool_calls, "raw": msg}

    def _anthropic_tools(self, messages, tools, system, temperature, max_tokens):
        ant_tools = []
        for t in tools:
            ant_tools.append({
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
            })
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "",
            messages=messages,
            tools=ant_tools if ant_tools else None,
            temperature=temperature,
        )
        text = ""
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "args": block.input or {}})
        return {"text": text, "tool_calls": tool_calls, "raw": resp, "stop_reason": resp.stop_reason}

    def _react_fallback(self, messages, tools, system, temperature, max_tokens):
        """ReAct testuale per provider senza tool calling nativo."""
        tool_desc = "\n".join(
            f"- {t['name']}: {t.get('description','')} | params: {json.dumps(t.get('parameters',{}))}"
            for t in tools
        )
        sys = (system or "") + (
            "\n\nHai accesso ai seguenti tool. Per usarne uno rispondi SOLO con JSON nel formato:\n"
            '{"tool": "<nome>", "args": {...}}\n'
            "Se non serve nessun tool, rispondi normalmente.\n"
            f"Tool disponibili:\n{tool_desc}"
        )
        text = self.chat(messages, system=sys, temperature=temperature, max_tokens=max_tokens)
        tool_calls = []
        # prova a estrarre JSON
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                obj = json.loads(text[start:end + 1])
                if "tool" in obj:
                    tool_calls.append({"id": "react-0", "name": obj["tool"], "args": obj.get("args", {})})
                    text = text[:start].strip() or text
        except Exception:
            pass
        return {"text": text, "tool_calls": tool_calls}

    def __repr__(self):
        return f"LLMClient(provider={self.provider}, model={self.model})"
