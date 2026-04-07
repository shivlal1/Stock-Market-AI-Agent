"""
Full PAHF 4-phase evaluation runner.

This automates the entire evaluation pipeline:
1. Creates agents with different configs (no memory, pre-only, post-only, PAHF)
2. Runs each through all 4 phases
3. Collects metrics and prints comparison tables
"""
from langchain_core.messages import HumanMessage
from tqdm import tqdm

from agent.graph import build_agent
from memory.manager import UserMemoryManager
from personas.profiles import PERSONAS, EVOLVED_PERSONAS
from personas.simulator import SimulatedUser
from evaluation.scenarios import SCENARIOS
from evaluation.metrics import success_rate, feedback_frequency, calculate_acpe
from config import LEARNING_ITERATIONS, MAX_PERSONAS_FOR_EVAL


def judge_relevance(response: str, persona: dict) -> bool:
    """Use LLM to judge if response was relevant to the persona."""
    from langchain_openai import ChatOpenAI
    from agent.prompts import JUDGE_PROMPT

    judge = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = JUDGE_PROMPT.format(
        user_profile=persona["profile"],
        user_sectors=", ".join(persona["sectors"]),
        user_holdings=", ".join(persona["holdings"]),
        response=response[:400],
    )
    result = judge.invoke([HumanMessage(content=prompt)])
    return "YES" in result.content.upper()


def run_single_interaction(agent, memory, sim_user, persona_id, persona,
                           scenario, enable_pre_fb, enable_post_fb):
    """Run one agent ↔ user interaction and return metrics."""

    # Step 1: Agent processes user query
    result = agent.invoke({
        "messages": [HumanMessage(content=scenario["query"])],
        "user_id": persona_id,
        "memory_context": "",
        "needs_clarification": False,
        "action_taken": "",
        "feedback_received": "",
        "session_notes": [],
    })

    agent_response = result["messages"][-1].content
    pre_feedback = 0
    post_feedback = 0

    # Step 2: Handle pre-action clarification
    if result.get("needs_clarification") and enable_pre_fb:
        pre_feedback = 1
        user_answer = sim_user.respond_to_clarification(agent_response)

        result = agent.invoke({
            "messages": result["messages"] + [HumanMessage(content=user_answer)],
            "user_id": persona_id,
            "memory_context": result.get("memory_context", ""),
            "needs_clarification": False,
            "action_taken": "",
            "feedback_received": "",
            "session_notes": [],
        })
        agent_response = result["messages"][-1].content

    # Step 3: Post-action feedback
    if enable_post_fb:
        feedback = sim_user.give_post_feedback(agent_response)

        is_negative = any(
            w in feedback.lower()
            for w in ["not interested", "wrong", "don't", "prefer", "instead",
                      "actually", "changed", "no longer", "sold", "switched"]
        )

        if is_negative:
            post_feedback = 1
            memory.update_from_feedback(persona_id, feedback, agent_response[:200])

        correct = not is_negative
    else:
        correct = judge_relevance(agent_response, persona)

    return {
        "persona_id": persona_id,
        "query": scenario["query"],
        "correct": correct,
        "pre_feedback": pre_feedback,
        "post_feedback": post_feedback,
    }


def run_phase(agent, memory, personas_dict, persona_ids, sim_users,
              scenarios, enable_pre_fb, enable_post_fb, phase_name):
    """Run one phase of evaluation."""
    results = []

    desc = f"{phase_name}"
    for persona_id in persona_ids:
        persona = personas_dict[persona_id]
        sim_user = sim_users[persona_id]

        for scenario in scenarios:
            result = run_single_interaction(
                agent, memory, sim_user, persona_id, persona,
                scenario, enable_pre_fb, enable_post_fb,
            )
            results.append(result)

    return results


def run_full_evaluation():
    """Run the complete PAHF 4-phase protocol and print results."""

    agent = build_agent()
    memory = UserMemoryManager()

    persona_ids = list(PERSONAS.keys())[:MAX_PERSONAS_FOR_EVAL]

    print(f"\nRunning evaluation with {len(persona_ids)} personas, "
          f"{len(SCENARIOS)} scenarios each, "
          f"{LEARNING_ITERATIONS} learning iterations\n")

    # ── Phase 1 ──
    print("=" * 60)
    print("PHASE 1: Initial Learning (original personas, feedback ON)")
    print("=" * 60)

    sim_users = {pid: SimulatedUser(PERSONAS[pid]) for pid in persona_ids}
    phase1_all = []

    for i in range(LEARNING_ITERATIONS):
        results = run_phase(
            agent, memory, PERSONAS, persona_ids, sim_users,
            SCENARIOS, enable_pre_fb=True, enable_post_fb=True,
            phase_name=f"Phase 1 iter {i + 1}",
        )
        phase1_all.append(results)
        sr = success_rate(results)
        ff = feedback_frequency(results)
        acpe = calculate_acpe(phase1_all)[-1]
        print(f"  Iter {i + 1}: SR={sr:.3f}, FF={ff:.3f}, ACPE={acpe:.3f}")

    # ── Phase 2 ──
    print(f"\n{'=' * 60}")
    print("PHASE 2: Test (original personas, feedback OFF)")
    print("=" * 60)

    results_p2 = run_phase(
        agent, memory, PERSONAS, persona_ids, sim_users,
        SCENARIOS, enable_pre_fb=False, enable_post_fb=False,
        phase_name="Phase 2",
    )
    print(f"  SR={success_rate(results_p2):.3f}")

    # ── Phase 3 ──
    print(f"\n{'=' * 60}")
    print("PHASE 3: Drift Adaptation (evolved personas, feedback ON)")
    print("=" * 60)

    evolved_sim_users = {
        pid: SimulatedUser(EVOLVED_PERSONAS.get(pid, PERSONAS[pid]))
        for pid in persona_ids
    }
    phase3_all = []

    for i in range(LEARNING_ITERATIONS):
        evolved_dict = {
            pid: EVOLVED_PERSONAS.get(pid, PERSONAS[pid])
            for pid in persona_ids
        }
        results = run_phase(
            agent, memory, evolved_dict, persona_ids, evolved_sim_users,
            SCENARIOS, enable_pre_fb=True, enable_post_fb=True,
            phase_name=f"Phase 3 iter {i + 1}",
        )
        phase3_all.append(results)
        sr = success_rate(results)
        ff = feedback_frequency(results)
        acpe = calculate_acpe(phase3_all)[-1]
        print(f"  Iter {i + 1}: SR={sr:.3f}, FF={ff:.3f}, ACPE={acpe:.3f}")

    # ── Phase 4 ──
    print(f"\n{'=' * 60}")
    print("PHASE 4: Post-Drift Test (evolved personas, feedback OFF)")
    print("=" * 60)

    evolved_dict = {
        pid: EVOLVED_PERSONAS.get(pid, PERSONAS[pid])
        for pid in persona_ids
    }
    results_p4 = run_phase(
        agent, memory, evolved_dict, persona_ids, evolved_sim_users,
        SCENARIOS, enable_pre_fb=False, enable_post_fb=False,
        phase_name="Phase 4",
    )
    print(f"  SR={success_rate(results_p4):.3f}")

    print(f"\n{'=' * 60}")
    print("EVALUATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_full_evaluation()