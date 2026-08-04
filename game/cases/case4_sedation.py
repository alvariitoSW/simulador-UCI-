"""Caso 4: Sedación y analgesia. Objetivo: lograr sedación ligera y objetivo (RASS -1 a 0)."""
from game.cases.base import BaseCase
from game.sim.patient import PatientState, clamp, approach
from game.ui.widgets import Button, Slider

TIME_LIMIT = 480.0
STABLE_HOLD_REQUIRED = 45.0
DEEP_CRITICAL_LIMIT = 60.0
AGITATION_CRITICAL_LIMIT = 50.0

RASS_DESCRIPTIONS = {
    4: "+4 Combativo: violento, peligro inmediato para el equipo.",
    3: "+3 Muy agitado: se retira tubos o catéteres, agresivo.",
    2: "+2 Agitado: movimientos frecuentes sin propósito, lucha con el ventilador.",
    1: "+1 Inquieto: ansioso, movimientos no agresivos.",
    0: "0 Alerta y calmado.",
    -1: "-1 Somnoliento: no plenamente alerta, despierta sostenidamente a la voz.",
    -2: "-2 Sedación leve: despierta brevemente a la voz.",
    -3: "-3 Sedación moderada: movimiento o apertura ocular a la voz (sin contacto visual).",
    -4: "-4 Sedación profunda: no responde a la voz, sí a estímulo físico.",
    -5: "-5 No despierta: sin respuesta a la voz ni al estímulo físico.",
}


class SedationCase(BaseCase):
    case_id = "sedation"
    title = "Sedación y analgesia"
    subtitle = "Paciente ventilado, agitado y luchando contra el ventilador"
    difficulty = "**"
    briefing = (
        "Un paciente conectado a ventilación mecánica está agitado (RASS +2), luchando contra "
        "el ventilador y con signos vitales elevados. Titula sedante (propofol) y analgesia "
        "(fentanilo) para lograr una sedación ligera y objetivo (RASS -1 a 0), evitando tanto "
        "la infrasedación como la sedación excesiva."
    )
    objectives = [
        "Titular propofol y fentanilo de forma progresiva",
        "Alcanzar y mantener RASS entre -1 y 0",
        "Evitar sedación profunda (hipotensión) y agitación peligrosa",
        "Reevaluar el RASS periódicamente",
    ]
    time_limit_s = TIME_LIMIT

    def __init__(self):
        super().__init__()
        self.state = PatientState(
            name="Paciente D - Sedación", age=45, weight_kg=75,
            hr=118, sbp=150, dbp=95, spo2=93, rr=26, temp=37.5,
            rhythm="sinusal", rass=2, intubated=True, on_vent=True,
        )
        self.state.add_log("Paciente agitado (RASS +2), luchando contra el ventilador.")
        self._rass_f = 2.0
        self.deep_critical_s = 0.0
        self.agitation_critical_s = 0.0

    def create_widgets(self, panel_rect):
        widgets = []
        x = panel_rect.x + 16
        w = panel_rect.width - 32
        y = panel_rect.y + 40

        def set_propofol(v):
            self.state.sedation_mcgkgmin = v

        def set_fentanil(v):
            self.state.analgesia_mcghr = v

        widgets.append(Slider((x, y + 20, w, 14), 0.0, 80.0, self.state.sedation_mcgkgmin,
                               step=2.0, label="Propofol", unit="mcg/kg/min", fmt="{:.0f}",
                               on_change=set_propofol))
        y += 60
        widgets.append(Slider((x, y + 20, w, 14), 0.0, 200.0, self.state.analgesia_mcghr,
                               step=5.0, label="Fentanilo", unit="mcg/h", fmt="{:.0f}",
                               on_change=set_fentanil))
        y += 60

        def eval_rass():
            r = self.state.rass
            desc = RASS_DESCRIPTIONS.get(r, str(r))
            self.state.add_log(f"Evaluación RASS: {desc}")

        widgets.append(Button((x, y, w, 36), "Evaluar RASS", eval_rass, size=16))
        return widgets

    def update(self, dt_sim, dt_real, cpr_tracker=None):
        if self.finished:
            return
        s = self.state
        s.time_s += dt_sim

        sedation_score = clamp(s.sedation_mcgkgmin / 80.0, 0.0, 1.0)
        analgesia_score = clamp(s.analgesia_mcghr / 200.0, 0.0, 1.0)
        combined = sedation_score * 1.0 + analgesia_score * 0.5
        target_rass_f = clamp(3.0 - combined * 7.0, -5.0, 4.0)
        self._rass_f = approach(self._rass_f, target_rass_f, 0.03, dt_sim)
        s.rass = int(round(self._rass_f))

        dev = self._rass_f - (-1.0)  # 0 cuando está en el objetivo (-1)
        hr_base, sbp_base, dbp_base, spo2_base, rr_base = 82.0, 122.0, 76.0, 96.0, 16.0
        if dev >= 0:
            hr_t = hr_base + dev * 10.0
            sbp_t = sbp_base + dev * 8.0
            dbp_t = dbp_base + dev * 5.0
            spo2_t = spo2_base - dev * 1.3
            rr_t = rr_base + dev * 3.0
        else:
            hr_t = hr_base + dev * 4.0
            sbp_t = sbp_base + dev * 11.0
            dbp_t = dbp_base + dev * 7.0
            spo2_t = spo2_base + dev * 1.0
            rr_t = rr_base + dev * 0.5

        s.hr = approach(s.hr, clamp(hr_t, 45, 165), 0.05, dt_sim)
        s.sbp = approach(s.sbp, clamp(sbp_t, 60, 175), 0.05, dt_sim)
        s.dbp = approach(s.dbp, clamp(dbp_t, 35, 110), 0.05, dt_sim)
        s.spo2 = approach(s.spo2, clamp(spo2_t, 80, 99), 0.05, dt_sim)
        s.rr = approach(s.rr, clamp(rr_t, 10, 34), 0.05, dt_sim)

        if s.map < 50:
            self.deep_critical_s += dt_sim
        else:
            self.deep_critical_s = max(0.0, self.deep_critical_s - dt_sim * 0.5)

        if s.rass >= 3:
            self.agitation_critical_s += dt_sim
        else:
            self.agitation_critical_s = max(0.0, self.agitation_critical_s - dt_sim * 0.5)

        stable = -1 <= s.rass <= 0
        if stable:
            self.elapsed_stable_s += dt_sim
        else:
            self.elapsed_stable_s = max(0.0, self.elapsed_stable_s - dt_sim)

        if self.elapsed_stable_s >= STABLE_HOLD_REQUIRED:
            time_bonus = max(0, (TIME_LIMIT - s.time_s) / TIME_LIMIT * 25)
            s.score(40, "Sedación objetivo alcanzada (RASS -1 a 0)")
            s.score(round(time_bonus), "Bonificación por rapidez")
            self.finish(True, "Sedación adecuada lograda",
                        "El paciente está tranquilo, sin signos de agitación ni de sedación "
                        "excesiva.",
                        ["La sedación ligera y dirigida por objetivo (RASS -1 a 0) reduce los "
                         "días de ventilación mecánica frente a la sedación profunda.",
                         "La analgesia adecuada (fentanilo) reduce la cantidad de sedante "
                         "necesaria."])
            return

        if self.deep_critical_s >= DEEP_CRITICAL_LIMIT:
            self.finish(False, "Sedación excesiva",
                        "La sedación profunda provocó hipotensión mantenida y compromiso "
                        "hemodinámico.",
                        ["Dosis altas de propofol pueden causar hipotensión significativa.",
                         "Titula la sedación al mínimo necesario para el objetivo de RASS."])
            return

        if self.agitation_critical_s >= AGITATION_CRITICAL_LIMIT:
            self.finish(False, "Autoextubación por agitación",
                        "La agitación no controlada llevó a que el paciente se retirara el "
                        "tubo endotraqueal, con riesgo vital inmediato.",
                        ["La agitación mantenida (RASS >= +3) es peligrosa en un paciente "
                         "intubado: aumenta sedación y/o analgesia sin demora."])
            return

        if s.time_s >= TIME_LIMIT:
            self.finish(False, "Tiempo agotado",
                        "No lograste alcanzar una sedación adecuada a tiempo.",
                        ["Ajusta la infusión de forma progresiva y reevalúa el RASS con "
                         "frecuencia."])
            return
