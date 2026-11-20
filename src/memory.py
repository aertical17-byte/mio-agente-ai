"""Memoria conversazionale (short-term + long-term semplice)."""
import json, os
from typing import List, Dict


class ConversationMemory:
    def __init__(self, path: str = None):
        self.messages: List[Dict[str, str]] = []
        self.path = path
        if path and os.path.exists(path):
            try:
                with open(path) as f:
                    self.messages = json.load(f)
            except Exception:
                self.messages = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get(self, last_n: int = None) -> List[Dict[str, str]]:
        if last_n:
            return self.messages[-last_n:]
        return list(self.messages)

    def clear(self):
        self.messages = []

    def save(self):
        if self.path:
            with open(self.path, "w") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def __len__(self):
        return len(self.messages)
