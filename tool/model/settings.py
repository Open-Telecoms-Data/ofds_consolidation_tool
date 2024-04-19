from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Percent 0-100
    nodes_merge_threshold: int
    nodes_ask_threshold: int

    nodes_match_radius_km: float
