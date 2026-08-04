"""Caso 2: Insuficiencia respiratoria aguda (SDRA). Objetivo: intubar y ventilar de forma protectora."""
from game.cases.base import BaseCase
from game.sim.patient import PatientState, clamp, approach
from game.sim.ventilator import default_vent_settings, peak_pressure, target_spo2_from_vent
from game.ui.widgets import Button, Slider, Toggle

TIME_LIMIT = 480.0
STABLE_HOLD_REQUIRED = 40.0
HYPOXIA_LIMIT = 60.0
BAROTRAUMA_LIMIT = 20.0


class ArdsCase(BaseCase):
    case_id = "ards"
    title = "Insuficiencia respiratoria aguda"
    subtitle = "Paciente de 54 años con neumonía bilateral y disnea progresiva"
    difficulty = "***"
    briefing = (
        "Un paciente de 54 años con neumonía bilateral se encuentra taquipneico e hipoxémico "
        "a pesar de oxígeno suplementario. Decide cuándo intubar y ajusta el ventilador con "
        "una estrategia de ventilación protectora (Vt bajo, PEEP y FiO2 adecuados)."
    )
    objectives = [
        "Reconocer la insuficiencia respiratoria que no mejora con oxígeno simple",
        "Intubar y conectar a ventilación mecánica a tiempo",
        "Usar volumen tidal protector (~6 ml/kg) y titular PEEP/FiO2",
        "Mantener SpO2 90-96% evitando presiones pico elevadas (barotrauma)",
    ]
    time_limit_s = TIME_LIMIT

    def __init__(self):
        super().__init__()
        self.state = PatientState(
            name="Paciente B - Insuf. respiratoria", age=54, weight_kg=72,
            hr=115, sbp=128, dbp=78, spo2=84, rr=32, temp=38.1,
            rhythm="sinusal",
        )
        self.state.add_log("Paciente taquipneico, SpO2 84% con mascarilla simple.")
        self.state.vent = default_vent_settings()
        self.o2_supp = True
        self.lung_severity = 0.62
        self.hypoxia_s = 0.0
        self.baro_s = 0.0
        self._vent_widgets = []

    def create_widgets(self, panel_rect):
        widgets = []
        x = panel_rect.x + 16
        w = panel_rect.width - 32
        y = panel_rect.y + 40

        def toggle_o2():
            self.o2_supp = not self.o2_supp

        o2_toggle = Toggle((x, y, w, 34), "Oxígeno suplementario", lambda: self.o2_supp, toggle_o2, size=16)
        widgets.append(o2_toggle)
        self._o2_toggle = o2_toggle
        y += 46

        def intubate():
            if not self.state.intubated:
                self.state.intubated = True
                self.state.on_vent = True
                self.state.add_log("Paciente intubado y conectado a ventilación mecánica.")

        intubate_btn = Button((x, y, w, 40), "Intubar y conectar a ventilador", intubate)
        widgets.append(intubate_btn)
        self._intubate_btn = intubate_btn
        y += 56

        def set_vt(v):
            self.state.vent["vt_ml_kg"] = v

        def set_peep(v):
            self.state.vent["peep"] = v

        def set_fio2(v):
            self.state.vent["fio2"] = v

        vt_slider = Slider((x, y + 20, w, 14), 4.0, 10.0, self.state.vent["vt_ml_kg"], step=0.5,
                            label="Volumen tidal", unit="ml/kg", fmt="{:.1f}", on_change=set_vt,
                            enabled=False)
        y += 56
        peep_slider = Slider((x, y + 20, w, 14), 0, 20, self.state.vent["peep"], step=1,
                              label="PEEP", unit="cmH2O", fmt="{:.0f}", on_change=set_peep,
                              enabled=False)
        y += 56
        fio2_slider = Slider((x, y + 20, w, 14), 21, 100, self.state.vent["fio2"], step=5,
                              label="FiO2", unit="%", fmt="{:.0f}", on_change=set_fio2,
                              enabled=False)
        widgets.extend([vt_slider, peep_slider, fio2_slider])
        self._vent_widgets = [vt_slider, peep_slider, fio2_slider]
        return widgets

    def update(self, dt_sim, dt_real, cpr_tracker=None):
        if self.finished:
            return
        s = self.state
        s.time_s += dt_sim

        if self._intubate_btn:
            self._intubate_btn.enabled = not s.intubated
        if self._o2_toggle:
            self._o2_toggle.enabled = not s.intubated
        for w in self._vent_widgets:
            w.enabled = s.intubated

        lung_compliance = clamp(1.0 - self.lung_severity * 0.7, 0.25, 1.0)

        if s.intubated:
            target_spo2 = target_spo2_from_vent(s.vent, self.lung_severity)
            pressure = peak_pressure(s.vent, lung_compliance)
            vt = s.vent["vt_ml_kg"]

            if pressure > 35:
                self.baro_s += dt_sim
                self.lung_severity = clamp(self.lung_severity + dt_sim * 0.002, 0.0, 1.0)
            else:
                self.baro_s = max(0.0, self.baro_s - dt_sim * 0.5)

            protective = 4.5 <= vt <= 8.0 and pressure <= 30
            well_oxygenated = 90 <= s.spo2 <= 97
            if protective and well_oxygenated:
                self.lung_severity = clamp(self.lung_severity - dt_sim * 0.0015, 0.05, 1.0)

            s.rr = approach(s.rr, s.vent["rr_set"], 0.08, dt_sim)
        else:
            target_spo2 = clamp(84 + (6 if self.o2_supp else 0) - (self.lung_severity - 0.3) * 30,
                                 55, 94)
            pressure = 0
            target_rr = clamp(32 + max(0, 88 - s.spo2) * 0.4, 20, 42)
            s.rr = approach(s.rr, target_rr, 0.05, dt_sim)

        s.spo2 = approach(s.spo2, target_spo2, 0.05, dt_sim)

        target_hr = clamp(78 + max(0, 92 - s.spo2) * 2.6, 70, 165)
        s.hr = approach(s.hr, target_hr, 0.05, dt_sim)

        if s.spo2 < 80:
            self.hypoxia_s += dt_sim
        else:
            self.hypoxia_s = max(0.0, self.hypoxia_s - dt_sim * 0.5)

        stable = s.intubated and 90 <= s.spo2 <= 97 and peak_pressure(
            s.vent, lung_compliance) <= 30
        if stable:
            self.elapsed_stable_s += dt_sim
        else:
            self.elapsed_stable_s = max(0.0, self.elapsed_stable_s - dt_sim)

        if self.elapsed_stable_s >= STABLE_HOLD_REQUIRED:
            time_bonus = max(0, (TIME_LIMIT - s.time_s) / TIME_LIMIT * 30)
            s.score(40, "Ventilación protectora lograda")
            s.score(round(time_bonus), "Bonificación por rapidez")
            self.finish(True, "Ventilación protectora lograda",
                        "La oxigenación se mantiene estable con parámetros ventilatorios seguros.",
                        ["Volumen tidal ~6 ml/kg reduce el riesgo de lesión pulmonar inducida "
                         "por el ventilador (VILI).",
                         "El PEEP ayuda a reclutar alvéolos colapsados; el FiO2 se titula para "
                         "evitar toxicidad por oxígeno mantenida en 100%.",
                         "Objetivo de SpO2 90-96%, no es necesario (ni deseable) buscar 100%."])
            return

        if self.hypoxia_s >= HYPOXIA_LIMIT:
            self.finish(False, "Hipoxemia refractaria",
                        "La saturación se mantuvo crítica demasiado tiempo, provocando paro "
                        "hipóxico.",
                        ["Si el oxígeno simple no basta, no demores la intubación.",
                         "Sube PEEP/FiO2 con decisión cuando la SpO2 esté crítica."])
            return

        if self.baro_s >= BAROTRAUMA_LIMIT:
            self.finish(False, "Barotrauma / neumotórax",
                        "Las presiones elevadas y el volumen tidal excesivo provocaron un "
                        "neumotórax a tensión.",
                        ["Vt > 8 ml/kg y presiones pico > 35 cmH2O aumentan mucho el riesgo de "
                         "lesión pulmonar.",
                         "Ante presiones altas, reduce el volumen tidal antes de seguir "
                         "subiendo PEEP."])
            return

        if s.time_s >= TIME_LIMIT:
            self.finish(False, "Tiempo agotado",
                        "No lograste estabilizar la ventilación a tiempo.",
                        ["No retrases la intubación cuando el oxígeno simple es insuficiente.",
                         "Ajusta PEEP y FiO2 de forma progresiva evaluando la respuesta."])
            return
