"""
Evaluation package — implements PAHF's 4-phase testing protocol.

Phase 1: Initial learning (feedback ON, original personas)
Phase 2: Evaluation (feedback OFF, original personas)
Phase 3: Drift adaptation (feedback ON, evolved personas)
Phase 4: Post-drift evaluation (feedback OFF, evolved personas)
"""
from evaluation.metrics import success_rate, feedback_frequency, calculate_acpe

__all__ = ["success_rate", "feedback_frequency", "calculate_acpe"]