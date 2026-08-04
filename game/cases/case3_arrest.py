"""Caso 3: Paro cardiorrespiratorio (ACLS). RCP, desfibrilación y epinefrina hasta lograr RCE."""
from game.cases.base import BaseCase
from game.sim.patient import PatientState, clamp, approach
from game.sim.cpr import attempt_shock
from game.ui.widgets import Button, Slider

PRE_ARREST_S = 12.0
EPI_INTERVAL = 180.0        # 3 minutos simulados entre dosis de epinefrina
MAX_ARREST_S = 480.0        # tiempo máximo acumulado en paro sin lograr RCE
STABLE_HOLD_REQUIRED = 30.0
POST_ROSC_CRITICAL_LIMIT = 30.0
TIME_LIMIT = 720.0


class ArrestCase(BaseCase):
    case_id = "arrest"
    title = "Paro cardiorrespiratorio (ACLS)"
    subtitle = "Paciente ingresado que súbitamente pierde el pulso"
    difficulty = "****"
    briefing = (
        "Un paciente monitorizado se deteriora súbitamente y entra en fibrilación ventricular. "
        "Inicia RCP de alta calidad, desfibrila cuando esté indicado y administra epinefrina "
        "según el protocolo ACLS hasta lograr el retorno de la circulación espontánea (RCE)."
    )
    objectives = [
        "Reconocer el paro y comenzar compresiones torácicas de inmediato",
        "Mantener una frecuencia de compresión de 100-120/min (barra espaciadora)",
        "Desfibrilar cuando el ritmo sea desfibrilable (FV / TV sin pulso)",
        "Administrar epinefrina 1 mg IV cada 3-5 minutos",
        "Estabilizar al paciente tras lograr el RCE",
    ]
    time_limit_s = TIME_LIMIT

    def __init__(self):
        super().__init__()
        self.state = PatientState(
            name="Paciente C - Paro cardiorrespiratorio", age=61, weight_kg=80,
            hr=98, sbp=104, dbp=68, spo2=95, rr=20, temp=37.2,
            rhythm="sinusal",
        )
        self.state.add_log("Paciente monitorizado, signos vitales límite.")
        self.phase = "pre_arrest"  # pre_arrest -> arrest -> rosc
        self.time_since_epi = EPI_INTERVAL
        self.cpr_quality_ema = 0.0
        self.arrest_accum_s = 0.0
        self.post_rosc_critical_s = 0.0
        self._shock_btn = None
        self._epi_btn = None

    # ---------------- UI ----------------
    def create_widgets(self, panel_rect):
        widgets = []
        x = panel_rect.x + 16
        w = panel_rect.width - 32
        y = panel_rect.y + 40

        shock_btn = Button((x, y, w, 44), "Descargar (200 J)", self.deliver_shock,
                            color=(120, 40, 40))
        widgets.append(shock_btn)
        self._shock_btn = shock_btn
        y += 60

        epi_btn = Button((x, y, w, 40), "Epinefrina 1 mg IV", self.give_epi)
        widgets.append(epi_btn)
        self._epi_btn = epi_btn
        y += 60

        def set_norepi(v):
            self.state.vasopressor_mcgkgmin = v

        widgets.append(Slider((x, y + 20, w, 14), 0.0, 1.0, self.state.vasopressor_mcgkgmin,
                               step=0.02, label="Noradrenalina (post-RCE)", unit="mcg/kg/min",
                               fmt="{:.2f}", on_change=set_norepi))
        return widgets

    def deliver_shock(self):
        s = self.state
        if self.phase != "arrest" or s.rhythm not in ("fv", "tvsp"):
            s.add_log("Descarga no indicada: el ritmo actual no es desfibrilable.")
            return
        time_in_arrest = s.time_s - s.arrest_time_s
        success = attempt_shock(time_in_arrest, self.cpr_quality_ema)
        s.shocks_delivered += 1
        s.add_log(f"Descarga #{s.shocks_delivered} administrada. Reanudando RCP...")
        if success:
            self._achieve_rosc()
        else:
            s.add_log("El ritmo persiste en fibrilación ventricular.")

    def give_epi(self):
        s = self.state
        if self.phase not in ("arrest",):
            s.add_log("La epinefrina se indica durante el paro, según protocolo ACLS.")
            return
        if s.epi_doses > 0 and self.time_since_epi < EPI_INTERVAL:
            s.score(-5, "Epinefrina administrada antes de lo indicado")
        else:
            s.score(8, "Epinefrina según protocolo (cada 3-5 min)")
        s.epi_doses += 1
        self.time_since_epi = 0.0
        s.add_log(f"Epinefrina 1 mg IV administrada (dosis #{s.epi_doses}).")

    def _achieve_rosc(self):
        s = self.state
        s.rhythm = "sinusal"
        s.hr = 96
        s.sbp = 96
        s.dbp = 62
        s.spo2 = 90
        s.rosc_time_s = s.time_s
        self.phase = "rosc"
        self.elapsed_stable_s = 0.0
        s.score(35, "Retorno de circulación espontánea (RCE)")
        s.add_log("¡RCE logrado! Ahora estabiliza al paciente.")

    # ---------------- Fisiología ----------------
    def update(self, dt_sim, dt_real, cpr_tracker=None):
        if self.finished:
            return
        s = self.state
        s.time_s += dt_sim
        self.time_since_epi += dt_sim

        if self._shock_btn:
            self._shock_btn.enabled = self.phase == "arrest" and s.rhythm in ("fv", "tvsp")
        if self._epi_btn:
            self._epi_btn.enabled = self.phase == "arrest"

        if self.phase == "pre_arrest":
            s.hr = approach(s.hr, 135, 0.06, dt_sim)
            s.sbp = approach(s.sbp, 84, 0.06, dt_sim)
            s.dbp = approach(s.dbp, 55, 0.06, dt_sim)
            s.spo2 = approach(s.spo2, 89, 0.06, dt_sim)
            if s.time_s >= PRE_ARREST_S:
                self.phase = "arrest"
                s.rhythm = "fv"
                s.conscious = False
                s.hr = 0
                s.spo2 = 0
                s.arrest_time_s = s.time_s
                s.add_log("¡Fibrilación ventricular! El paciente no responde ni tiene pulso.")
            return

        if self.phase == "arrest":
            q = cpr_tracker.quality() if cpr_tracker else 0.0
            self.cpr_quality_ema = self.cpr_quality_ema * 0.92 + q * 0.08
            self.arrest_accum_s += dt_sim
            if self.arrest_accum_s >= MAX_ARREST_S:
                self.finish(False, "No se logró el RCE",
                            "A pesar de la reanimación, no se logró recuperar la circulación "
                            "espontánea en un tiempo razonable.",
                            ["La calidad de las compresiones (frecuencia 100-120/min, mínimas "
                             "interrupciones) es determinante para el éxito de la RCP.",
                             "Desfibrila cuanto antes cuando el ritmo sea desfibrilable.",
                             "No olvides la epinefrina cada 3-5 minutos según ACLS."])
            return

        if self.phase == "rosc":
            target_map = clamp(58.0 + s.vasopressor_mcgkgmin * 35.0, 45.0, 100.0)
            target_sbp = target_map + 25.0
            target_dbp = target_map - 15.0
            s.sbp = approach(s.sbp, target_sbp, 0.05, dt_sim)
            s.dbp = approach(s.dbp, target_dbp, 0.05, dt_sim)
            target_hr = clamp(130.0 - (target_map - 55.0) * 1.0, 65.0, 150.0)
            s.hr = approach(s.hr, target_hr, 0.05, dt_sim)
            s.spo2 = approach(s.spo2, 96.0, 0.03, dt_sim)

            if s.map < 45:
                self.post_rosc_critical_s += dt_sim
            else:
                self.post_rosc_critical_s = max(0.0, self.post_rosc_critical_s - dt_sim * 0.5)

            if self.post_rosc_critical_s >= POST_ROSC_CRITICAL_LIMIT:
                self.phase = "arrest"
                s.rhythm = "asistolia"
                s.hr = 0
                s.spo2 = 0
                s.arrest_time_s = s.time_s
                self.arrest_accum_s = 0.0
                s.add_log("La hipotensión mantenida provoca un nuevo paro (asistolia).")
                return

            stable = s.map >= 65 and s.spo2 >= 90 and s.hr < 120
            if stable:
                self.elapsed_stable_s += dt_sim
            else:
                self.elapsed_stable_s = max(0.0, self.elapsed_stable_s - dt_sim)

            if self.elapsed_stable_s >= STABLE_HOLD_REQUIRED:
                time_bonus = max(0, (TIME_LIMIT - s.time_s) / TIME_LIMIT * 25)
                s.score(30, "Paciente estabilizado tras el RCE")
                s.score(round(time_bonus), "Bonificación por rapidez")
                self.finish(True, "RCE logrado y paciente estable",
                            "Lograste revertir el paro cardiorrespiratorio y estabilizar al "
                            "paciente tras la reanimación.",
                            ["Las compresiones de alta calidad y la desfibrilación precoz "
                             "aumentan mucho la probabilidad de RCE.",
                             "Tras el RCE, sostener la presión arterial (vasopresor si hace "
                             "falta) evita un nuevo paro."])
                return

        if s.time_s >= TIME_LIMIT:
            self.finish(False, "Tiempo agotado",
                        "No lograste estabilizar al paciente dentro del tiempo disponible.",
                        ["Actúa con el algoritmo ACLS: RCP continua, descarga si procede y "
                         "epinefrina programada."])
            return
