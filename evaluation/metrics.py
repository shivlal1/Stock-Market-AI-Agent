"""
Evaluation metrics matching the PAHF paper.

Three metrics:
- Success Rate (SR): fraction of correct/relevant responses
- Feedback Frequency (FF): how often feedback was needed
- ACPE: Average Cumulative Personalization Error (tracks learning over time)
"""


def success_rate(results: list) -> float:
    """Fraction of interactions where agent was relevant/correct."""
    if not results:
        return 0.0
    correct = sum(1 for r in results if r.get("correct", False))
    return correct / len(results)


def feedback_frequency(results: list) -> float:
    """Fraction of interactions that used any feedback channel."""
    if not results:
        return 0.0
    fb_count = sum(
        1 for r in results
        if r.get("pre_feedback", 0) or r.get("post_feedback", 0)
    )
    return fb_count / len(results)


def calculate_acpe(phase_results: list) -> list:
    """
    Average Cumulative Personalization Error across iterations.

    ACPE_t = (1/t) * sum(PE_1 ... PE_t)
    where PE_t = 1 - SR_t

    This metric from the PAHF paper shows how quickly the agent
    reduces its error over repeated interactions. A steeply
    declining ACPE = the agent is learning fast.

    Args:
        phase_results: List of result lists, one per iteration.
                       e.g., [iter1_results, iter2_results, iter3_results]

    Returns:
        List of ACPE values, one per iteration.
    """
    acpe_values = []
    cumulative_error = 0.0

    for t, result_set in enumerate(phase_results, 1):
        sr = success_rate(result_set)
        pe = 1.0 - sr  # personalization error
        cumulative_error += pe
        acpe = cumulative_error / t
        acpe_values.append(round(acpe, 4))

    return acpe_values