"""
Orchestratore multi-agente.

Pattern implementati (ispirati a Microsoft ai-agents-for-beginners lessons 03, 07, 08):
  - Sequential pipeline: Planner -> Researcher -> Coder -> Reviewer
  - Review loop: il Reviewer puo' rimandare al Coder (max N iterazioni)
  - Parallel fan-out: piu' agenti lavorano in parallelo su sotto-task
  - Handoff: il Coordinator smista la richiesta

Tutto eseguito in-process, nessun servizio esterno richiesto oltre all'LLM.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable

from src.agents.base import BaseAgent
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearcherAgent
from src.agents.coder import CoderAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.coordinator import CoordinatorAgent


class MultiAgentOrchestrator:
    def __init__(self, llm=None, max_review_iterations: int = 2):
        self.llm = llm
        self.planner = PlannerAgent(llm)
        self.researcher = ResearcherAgent(llm)
        self.coder = CoderAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        self.coordinator = CoordinatorAgent(llm)
        self.max_review_iterations = max_review_iterations

    def reset(self):
        for a in (self.planner, self.researcher, self.coder, self.reviewer, self.coordinator):
            a.reset_memory()

    # ---------- sequential pipeline ----------
    def run_pipeline(self, task: str, on_step: Callable[[str, str], None] = None) -> Dict[str, Any]:
        trace = []
        def emit(agent, out):
            trace.append({"agent": agent, "output": out})
            if on_step:
                on_step(agent, out)

        plan = self.planner.think(task)
        emit("Planner", plan)

        research = self.researcher.think(
            "Ricerca le informazioni necessarie per eseguire questo piano.",
            context=f"TASK:\n{task}\n\nPIANO:\n{plan}",
        )
        emit("Researcher", research)

        code = self.coder.think(
            "Produci la soluzione (codice o risposta operativa) seguendo piano e ricerca.",
            context=f"TASK:\n{task}\n\nPIANO:\n{plan}\n\nRICERCA:\n{research}",
        )
        emit("Coder", code)

        # review loop
        review = ""
        for i in range(self.max_review_iterations):
            review = self.reviewer.think(
                "Revisiona il lavoro prodotto. Se ci sono problemi gravi, indica 'DA RIVEDERE' e spiega cosa correggere.",
                context=f"TASK:\n{task}\n\nPIANO:\n{plan}\n\nRICERCA:\n{research}\n\nSOLUZIONE:\n{code}",
            )
            emit(f"Reviewer (iter {i+1})", review)
            if "DA RIVEDERE" not in review.upper():
                break
            # rimanda al coder con il feedback
            code = self.coder.think(
                "Correggi la soluzione in base al feedback del revisore.",
                context=f"TASK:\n{task}\n\nFEEDBACK REVISORE:\n{review}\n\nSOLUZIONE PRECEDENTE:\n{code}",
            )
            emit(f"Coder (revisione {i+1})", code)

        final = self.coordinator.think(
            "Sintetizza il risultato finale per l'utente, in italiano, chiaro e completo.",
            context=f"TASK:\n{task}\n\nPIANO:\n{plan}\n\nRICERCA:\n{research}\n\nSOLUZIONE:\n{code}\n\nREVISIONE:\n{review}",
        )
        emit("Coordinator", final)

        return {"task": task, "plan": plan, "research": research,
                "solution": code, "review": review, "final": final, "trace": trace}

    # ---------- parallel fan-out ----------
    def run_parallel(self, task: str, subtasks: List[str],
                     on_step: Callable[[str, str], None] = None) -> Dict[str, Any]:
        """Esegue piu' agenti in parallelo su sotto-task, poi aggrega."""
        results = {}
        with ThreadPoolExecutor(max_workers=len(subtasks)) as ex:
            futures = {}
            for i, st in enumerate(subtasks):
                agent = self.researcher if i % 2 == 0 else self.coder
                futures[ex.submit(agent.think, st)] = (i, agent.name)
            for fut in as_completed(futures):
                i, name = futures[fut]
                out = fut.result()
                results[i] = {"agent": name, "output": out}
                if on_step:
                    on_step(f"{name} (task {i})", out)
        aggregated = "\n\n".join(
            f"[Agente {results[i]['agent']} - task {i}]\n{results[i]['output']}"
            for i in sorted(results)
        )
        final = self.coordinator.think(
            "Sintetizza i risultati paralleli in una risposta unica.",
            context=f"TASK:\n{task}\n\nRISULTATI PARALLELI:\n{aggregated}",
        )
        if on_step:
            on_step("Coordinator", final)
        return {"task": task, "parallel": results, "final": final}

    # ---------- handoff ----------
    def run_handoff(self, task: str, on_step: Callable[[str, str], None] = None) -> Dict[str, Any]:
        """Il Coordinator decide quale agente attivare e in che ordine (loop)."""
        # Step 1: coordinator produce un piano di handoff
        decision = self.coordinator.think(
            "Analizza la richiesta e decidi: quali agenti attivare (tra Planner, Researcher, Coder, Reviewer) "
            "e in che ordine. Rispondi con una lista di nomi separati da virgola, es: 'Planner, Researcher, Coder'.",
            context=f"TASK:\n{task}",
        )
        if on_step:
            on_step("Coordinator (handoff decision)", decision)
        agents_map = {
            "planner": self.planner, "researcher": self.researcher,
            "coder": self.coder, "reviewer": self.reviewer,
        }
        chosen = []
        for token in decision.replace(",", " ").split():
            key = token.strip().lower().rstrip(".,;:")
            if key in agents_map and agents_map[key] not in chosen:
                chosen.append(agents_map[key])
        if not chosen:
            chosen = [self.planner, self.researcher, self.coder]

        context = f"TASK:\n{task}"
        outputs = {}
        for ag in chosen:
            out = ag.think("Esegui il tuo ruolo per questo task.", context=context)
            outputs[ag.name] = out
            context += f"\n\n[{ag.name}]\n{out}"
            if on_step:
                on_step(ag.name, out)

        final = self.coordinator.think(
            "Sintetizza il risultato finale.", context=f"TASK:\n{task}\n\n" + context
        )
        if on_step:
            on_step("Coordinator (finale)", final)
        return {"task": task, "decision": decision, "outputs": outputs, "final": final}
