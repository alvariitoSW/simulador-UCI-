"""Estado fisiológico del paciente y utilidades comunes."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def approach(current, target, rate, dt):
    """Mueve `current` hacia `target` a una tasa proporcional (respuesta exponencial)."""
    return current + (target - current) * min(1.0, rate * dt)


@dataclass
class PatientState:
    name: str = "Paciente"
    age: int = 60
    weight_kg: float = 70.0

    hr: float = 80.0
    sbp: float = 120.0
    dbp: float = 80.0
    spo2: float = 98.0
    rr: float = 16.0
    temp: float = 37.0
    lactate: float = 1.4

    rhythm: str = "sinusal"  # sinusal, taquicardia, fv, tvsp, asistolia, aesp
    rass: int = 0            # -5 (coma) .. +4 (agitación peligrosa)
    conscious: bool = True
    apnea: bool = False

    intubated: bool = False
    on_vent: bool = False
    vent: Dict[str, Any] = field(default_factory=dict)

    fluids_ml: float = 0.0
    vasopressor_mcgkgmin: float = 0.0
    sedation_mcgkgmin: float = 0.0   # propofol
    analgesia_mcghr: float = 0.0     # fentanilo
    antibiotics_given: bool = False
    epi_doses: int = 0
    shocks_delivered: int = 0

    time_s: float = 0.0
    arrest_time_s: float = 0.0
    rosc_time_s: float = 0.0
    log: List[str] = field(default_factory=list)
    score_events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def map(self):
        return self.dbp + (self.sbp - self.dbp) / 3.0

    def add_log(self, msg):
        self.log.append(msg)
        if len(self.log) > 8:
            self.log.pop(0)

    def score(self, points, reason):
        self.score_events.append({"points": points, "reason": reason, "t": self.time_s})

    @property
    def total_score(self):
        return sum(e["points"] for e in self.score_events)


DANGEROUS_RHYTHMS = ("fv", "tvsp", "asistolia", "aesp")


def vitals_alarm(state: PatientState) -> bool:
    from game.constants import NORMAL_RANGES

    if state.rhythm in DANGEROUS_RHYTHMS:
        return True
    lo, hi = NORMAL_RANGES["hr"]
    if not (lo <= state.hr <= hi):
        return True
    lo, hi = NORMAL_RANGES["map"]
    if not (lo <= state.map <= hi):
        return True
    lo, hi = NORMAL_RANGES["spo2"]
    if state.spo2 < lo:
        return True
    lo, hi = NORMAL_RANGES["rr"]
    if not (lo <= state.rr <= hi):
        return True
    return False
