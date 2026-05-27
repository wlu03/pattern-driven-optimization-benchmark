from dataclasses import dataclass


@dataclass
class PatternEntry:
    pattern_id: str          # e.g., "SR-1"
    category: str            # e.g., "Semantic Redundancy"
    name: str                # e.g., "Loop-Invariant Semantic Computation"
    slow_code: str           # The inefficient C code
    fast_code: str           # Hand-optimized reference
    test_harness: str        # Code to call and verify the function
    compiler_difficulty: str  # "Low", "Medium", "High", "Very High"
    description: str         # What the inefficiency is
