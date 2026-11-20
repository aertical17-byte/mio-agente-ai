#!/usr/bin/env python3
"""CLI per il sistema multi-agente. Tutto nel cloud / in-process."""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm_client import LLMClient
from src.orchestrator import MultiAgentOrchestrator
from src.memory import ConversationMemory


def print_step(agent, out):
    print(f"\n{'='*70}")
    print(f"🤖 {agent}")
    print(f"{'='*70}")
    print(out)


def main():
    parser = argparse.ArgumentParser(description="Sistema multi-agente AI intelligente")
    parser.add_argument("task", nargs="?", help="Task da eseguire")
    parser.add_argument("--mode", choices=["pipeline", "parallel", "handoff"], default="pipeline")
    parser.add_argument("--provider", default=None, help="Provider LLM (anthropic, openai, groq, ...)")
    parser.add_argument("--model", default=None, help="Nome modello")
    parser.add_argument("--interactive", action="store_true", help="Modalita' chat interattiva")
    args = parser.parse_args()

    llm = LLMClient(provider=args.provider, model=args.model)
    print(f"[LLM] {llm}")

    orch = MultiAgentOrchestrator(llm=llm)
    mem = ConversationMemory()

    if args.interactive:
        print("Modalita' interattiva. Scrivi 'exit' per uscire, 'reset' per pulire la memoria.")
        while True:
            try:
                q = input("\nTu> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not q:
                continue
            if q.lower() in ("exit", "quit"):
                break
            if q.lower() == "reset":
                orch.reset()
                mem.clear()
                print("Memoria pulita.")
                continue
            mem.add("user", q)
            res = orch.run_pipeline(q, on_step=print_step)
            mem.add("assistant", res["final"])
            print(f"\n{'#'*70}\nRISULTATO FINALE:\n{res['final']}\n{'#'*70}")
        mem.save()
        return

    if not args.task:
        parser.print_help()
        sys.exit(1)

    if args.mode == "pipeline":
        res = orch.run_pipeline(args.task, on_step=print_step)
    elif args.mode == "parallel":
        # sotto-task di esempio: l'utente puo' passarli con --subtasks
        subs = [args.task]
        res = orch.run_parallel(args.task, subs, on_step=print_step)
    else:
        res = orch.run_handoff(args.task, on_step=print_step)

    print(f"\n{'#'*70}\nRISULTATO FINALE:\n{res['final']}\n{'#'*70}")


if __name__ == "__main__":
    main()
