# AI-GENERATED FILE (Claude, 2026-11-21) | reviewed by: Chris
from sentinel.models import ComponentScores, FatigueState


class OfflineSensor:
    """Stand-in for a sensor that isn't merged yet: always returns its 'empty' data."""

    def __init__(self, name: str, empty) -> None:
        self.name = name
        self.empty = empty

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def snapshot(self):
        return self.empty


class PlaceholderModel:
    """Temporary scorer until Keyboard's FatigueModel is merged."""

    def update(self, features) -> FatigueState:
        score = min(100.0, features.mouse.clicks * 5.0)   # any simple formula
        return FatigueState(
            schema_version="1.1", timestamp="", seq=0, interval_s=5.0,
            systemic_fatigue_score=score, level="low", trend_per_min=0.0,
            components=ComponentScores(0, 0, 0, 0), top_contributors=[],
            activity_state="active", flow=False, calibrating=True,
            sensors={"keyboard": features.keyboard.available, "mouse": features.mouse.available,
                     "context": features.context.available, "vision": features.vision.available},
            signals={},
        )


class NoInterventions:
    """Temporary reminder engine until Webcam's InterventionEngine is merged."""

    def evaluate(self, state, features):
        return None