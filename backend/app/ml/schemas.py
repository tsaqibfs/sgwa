from dataclasses import dataclass


@dataclass(frozen=True)
class Prediction:
    agency_code: str
    probabilities: dict[str, float]
    confidence: float
    known_features: bool
    model_version: str
