"""
Personas package — synthetic user profiles for evaluation.

Contains investor personas (original + evolved versions) and
an LLM-based simulator that acts as a human user during testing.
"""
from personas.profiles import PERSONAS, EVOLVED_PERSONAS
from personas.simulator import SimulatedUser

__all__ = ["PERSONAS", "EVOLVED_PERSONAS", "SimulatedUser"]