"""
Tool (funzioni) usati dagli agenti.

I pattern (decorator @tool, tipizzazione Annotated, approval_mode) sono ispirati a:
  Microsoft ai-agents-for-beginners (https://github.com/microsoft/ai-agents-for-beginners)
  Licenza MIT. Crediti a Microsoft Corporation.

Tutti i tool girano nel cloud / in-process: nessuna installazione locale richiesta.
"""
import os
import json
import math
import subprocess
import tempfile
from typing import Annotated, List, Dict, Any
from datetime import datetime


# ---------- tool registry ----------
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str = None, description: str = "", approval_mode: str = "never_require"):
    """Decorator per registrare un tool. Ispirato a @tool di Microsoft Agent Framework."""
    def decorator(fn):
        tname = name or fn.__name__
        # estrai schema dai type hints (semplificato)
        import inspect
        sig = inspect.signature(fn)
        props = {}
        required = []
        for pname, param in sig.parameters.items():
            ann = param.annotation
            ptype = "string"
            if ann in (int, float):
                ptype = "number"
            elif ann is bool:
                ptype = "boolean"
            elif ann in (list, List):
                ptype = "array"
            elif ann in (dict, Dict):
                ptype = "object"
            props[pname] = {"type": ptype, "description": pname}
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        schema = {"type": "object", "properties": props, "required": required}
        TOOL_REGISTRY[tname] = {
            "name": tname,
            "description": description or (fn.__doc__ or "").strip(),
            "parameters": schema,
            "fn": fn,
            "approval_mode": approval_mode,
        }
        fn._tool_name = tname
        return fn
    return decorator


def get_tool(name: str):
    return TOOL_REGISTRY.get(name)


def list_tools() -> List[Dict[str, Any]]:
    return [{"name": v["name"], "description": v["description"], "parameters": v["parameters"]}
            for v in TOOL_REGISTRY.values()]


def call_tool(name: str, args: Dict[str, Any]) -> Any:
    t = TOOL_REGISTRY.get(name)
    if not t:
        return f"Tool '{name}' non trovato."
    try:
        return t["fn"](**(args or {}))
    except Exception as e:
        return f"Errore nel tool {name}: {e}"


# ---------- tool implementations ----------

@tool(name="calculator", description="Calcola un'espressione matematica. Es: '2+2', 'sqrt(16)', 'sin(pi/2)'.")
def calculator(expression: Annotated[str, "Espressione matematica da valutare"]) -> str:
    # safe eval con solo math
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Errore: {e}"


@tool(name="get_current_datetime", description="Restituisce data e ora corrente UTC.")
def get_current_datetime() -> str:
    return datetime.utcnow().isoformat() + "Z"


@tool(name="web_search", description="Cerca sul web (DuckDuckGo, nessuna chiave). Ritorna titoli e snippet.")
def web_search(query: Annotated[str, "Query di ricerca"]) -> str:
    try:
        import requests
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        out = []
        if data.get("AbstractText"):
            out.append(f"Riassunto: {data['AbstractText']}")
        for t in data.get("RelatedTopics", [])[:8]:
            if isinstance(t, dict) and t.get("Text"):
                out.append(f"- {t['Text']}")
        if not out:
            out.append("Nessun risultato diretto. Prova a riformulare la query.")
        return "\n".join(out)
    except Exception as e:
        return f"Errore ricerca: {e}"


@tool(name="run_python", description="Esegue codice Python in un subprocess isolato (cloud/container). Ritorna stdout/stderr.")
def run_python(code: Annotated[str, "Codice Python da eseguire"]) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            ["python3", path],
            capture_output=True, text=True, timeout=60,
        )
        out = proc.stdout
        if proc.stderr:
            out += "\n[STDERR]\n" + proc.stderr
        if proc.returncode != 0:
            out += f"\n[exit code {proc.returncode}]"
        return out.strip() or "(nessun output)"
    except subprocess.TimeoutExpired:
        return "Timeout: esecuzione oltre 60s."
    except Exception as e:
        return f"Errore: {e}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


@tool(name="read_file", description="Legge un file di testo (path locale nel container cloud).")
def read_file(path: Annotated[str, "Percorso del file"]) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:8000]
    except Exception as e:
        return f"Errore lettura: {e}"


@tool(name="write_file", description="Scrive un file di testo (path locale nel container cloud).")
def write_file(path: Annotated[str, "Percorso del file"], content: Annotated[str, "Contenuto da scrivere"]) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File scritto: {path} ({len(content)} caratteri)"
    except Exception as e:
        return f"Errore scrittura: {e}"


@tool(name="list_directory", description="Elenca i file di una directory.")
def list_directory(path: Annotated[str, "Percorso directory"] = ".") -> str:
    try:
        entries = sorted(os.listdir(path))
        return "\n".join(entries) if entries else "(vuota)"
    except Exception as e:
        return f"Errore: {e}"


# Auto-registra i tool built-in quando il modulo viene importato
BUILTIN_TOOLS = list_tools()
BUILTIN_TOOL_NAMES = [t["name"] for t in BUILTIN_TOOLS]
