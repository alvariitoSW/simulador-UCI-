"""Modelo simplificado de ventilador mecánico."""
from game.sim.patient import clamp


def default_vent_settings():
    return {
        "mode": "VCV",       # VCV (volumen control) o PCV (presión control)
        "vt_ml_kg": 6.0,     # volumen tidal por kg de peso ideal (objetivo protector: 6 ml/kg)
        "peep": 5,           # cmH2O
        "fio2": 50,          # %
        "rr_set": 16,        # respiraciones por minuto programadas
    }


def peak_pressure(vent, lung_compliance=1.0):
    """Estimación simplificada de la presión pico (cmH2O) según Vt, PEEP y distensibilidad."""
    vt = vent["vt_ml_kg"]
    peep = vent["peep"]
    base = vt * 1.6 / max(0.2, lung_compliance)
    return peep + base


def target_spo2_from_vent(vent, lung_severity):
    """Devuelve una SpO2 objetivo aproximada según FiO2/PEEP y la severidad del daño pulmonar
    (0 = pulmón sano, 1 = SDRA severo)."""
    fio2 = vent["fio2"]
    peep = vent["peep"]
    oxygenation = (fio2 - 21) * 0.62 + (peep - 5) * 2.0
    penalty = lung_severity * 55.0
    target = 84 + oxygenation - penalty
    return clamp(target, 55, 100)
