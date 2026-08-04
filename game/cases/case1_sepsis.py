"""Caso 1: Shock séptico. Objetivo: reanimación con fluidos, vasopresor y antibiótico precoz."""
import pygame

from game.cases.base import BaseCase
from game.sim.patient import PatientState, clamp, approach
from game.ui.widgets import Button, Slider, Toggle

TIME_LIMIT = 480.0          # 8 minutos simulados para estabilizar
STABLE_HOLD_REQUIRED = 40.0  # segundos simulados estables y seguidos para ganar
CRITICAL_HOLD_LIMIT = 100.0  # segundos con TAM crítica antes de perder
MAX_SAFE_FLUIDS = 3000.0
FLUID_DEATH_LEVEL = 7000.0


class SepsisCase(BaseCase):
    case_id = "sepsis"
    title = "Shock séptico"
    subtitle = "Paciente de 68 años, foco urinario, hipotenso y taquicárdico"
    difficulty = "**"
    briefing = (
        "Un paciente de 68 años ingresa con fiebre, confusión leve e hipotensión tras una "
        "infección urinaria. Sospechas shock séptico. Reanima con fluidos, inicia "
        "vasopresor si es necesario y no olvides los antibióticos precoces."
    )
    objectives = [
        "Administrar cristaloides (bolos de 500 ml) de forma juiciosa",
        "Iniciar noradrenalina si la TAM sigue < 65 mmHg tras fluidos",
        "Administrar antibiótico de amplio espectro cuanto antes",
        "Mantener TAM >= 65 mmHg y lactato en descenso",
    ]
    time_limit_s = TIME_LIMIT

    def __init__(self):
        super().__init__()
        self.state = PatientState(
            name="Paciente A - Shock séptico", age=68, weight_kg=78,
            hr=128, sbp=82, dbp=48, spo2=93, rr=24, temp=39.3, lactate=4.2,
            rhythm="sinusal",
        )
        self.state.add_log("Ingresa paciente con sospecha de shock séptico.")
        self.critical_s = 0.0
        self.overload_critical_s = 0.0
        self._abx_bonus_given = False

    # ---------------- UI ----------------
    def create_widgets(self, panel_rect):
        widgets = []
        x = panel_rect.x + 16
        w = panel_rect.width - 32
        y = panel_rect.y + 40

        def give_fluids():
            self.state.fluids_ml += 500
            self.state.add_log(f"Bolo de 500 ml administrado (total {self.state.fluids_ml:.0f} ml).")

        widgets.append(Button((x, y, w, 40), "Bolo de cristaloides (+500 ml)", give_fluids))
        y += 56

        def give_abx():
            if not self.state.antibiotics_given:
                self.state.antibiotics_given = True
                self.state.add_log("Antibiótico de amplio espectro administrado.")
                if not self._abx_bonus_given and self.state.time_s < 120:
                    self.state.score(20, "Antibiótico precoz (<2 min)")
                    self._abx_bonus_given = True

        abx_btn = Button((x, y, w, 40), "Administrar antibiótico", give_abx)
        widgets.append(abx_btn)
        self._abx_btn = abx_btn
        y += 56

        def check_lactate():
            self.state.add_log(f"Lactato actual: {self.state.lactate:.1f} mmol/L.")

        widgets.append(Button((x, y, w, 34), "Reevaluar lactato", check_lactate, size=16))
        y += 50

        def set_norepi(v):
            self.state.vasopressor_mcgkgmin = v

        widgets.append(Slider((x, y + 20, w, 14), 0.0, 1.0, self.state.vasopressor_mcgkgmin,
                               step=0.02, label="Noradrenalina", unit="mcg/kg/min",
                               fmt="{:.2f}", on_change=set_norepi))
        return widgets

    # ---------------- Fisiología ----------------
    def update(self, dt_sim, dt_real, cpr_tracker=None):
        if self.finished:
            return
        s = self.state
        s.time_s += dt_sim

        if self._abx_btn:
            self._abx_btn.enabled = not s.antibiotics_given

        fluid_effect = min(s.fluids_ml, MAX_SAFE_FLUIDS) / MAX_SAFE_FLUIDS * 12.0
        overload_ml = max(0.0, s.fluids_ml - MAX_SAFE_FLUIDS)
        overload_penalty = min(18.0, overload_ml / 1000.0 * 6.0)
        vaso_effect = s.vasopressor_mcgkgmin * 35.0

        target_map = clamp(55.0 + fluid_effect + vaso_effect - overload_penalty * 0.3, 35.0, 100.0)
        target_sbp = target_map + 25.0
        target_dbp = target_map - 15.0
        s.sbp = approach(s.sbp, target_sbp, 0.05, dt_sim)
        s.dbp = approach(s.dbp, target_dbp, 0.05, dt_sim)

        target_hr = clamp(150.0 - (target_map - 55.0) * 4.2 + overload_penalty * 1.4, 68.0, 165.0)
        s.hr = approach(s.hr, target_hr, 0.04, dt_sim)

        target_spo2 = clamp(95.0 - overload_penalty * 1.1, 78.0, 99.0)
        s.spo2 = approach(s.spo2, target_spo2, 0.03, dt_sim)

        target_rr = clamp(23.0 - (target_map - 55.0) * 0.06 + overload_penalty * 0.9
                           + max(0.0, 94.0 - s.spo2) * 0.3, 14.0, 40.0)
        s.rr = approach(s.rr, target_rr, 0.05, dt_sim)

        if s.antibiotics_given:
            s.temp = approach(s.temp, 37.0, 0.01, dt_sim)
        else:
            s.temp = clamp(s.temp + dt_sim * 0.001, 36.5, 40.5)

        if s.map >= 65:
            s.lactate = approach(s.lactate, 0.9, 0.01, dt_sim)
        elif s.map < 50:
            s.lactate = clamp(s.lactate + dt_sim * 0.01, 0.5, 12.0)

        # --- condiciones de fin ---
        if s.map < 50:
            self.critical_s += dt_sim
        else:
            self.critical_s = max(0.0, self.critical_s - dt_sim * 0.5)

        if s.fluids_ml >= FLUID_DEATH_LEVEL and s.spo2 < 80:
            self.overload_critical_s += dt_sim
        else:
            self.overload_critical_s = max(0.0, self.overload_critical_s - dt_sim * 0.5)

        stable = (s.map >= 65 and s.hr < 110 and s.spo2 >= 92 and s.antibiotics_given
                  and s.lactate < 2.5)
        if stable:
            self.elapsed_stable_s += dt_sim
        else:
            self.elapsed_stable_s = max(0.0, self.elapsed_stable_s - dt_sim)

        if self.elapsed_stable_s >= STABLE_HOLD_REQUIRED:
            time_bonus = max(0, (TIME_LIMIT - s.time_s) / TIME_LIMIT * 30)
            s.score(40, "Paciente estabilizado")
            s.score(round(time_bonus), "Bonificación por rapidez")
            debrief = [
                "Reconociste el shock séptico y reanimaste con fluidos de forma escalonada.",
                "Iniciaste noradrenalina para sostener la TAM >= 65 mmHg.",
                "El antibiótico precoz es clave: reduce la mortalidad de forma significativa.",
            ]
            if s.fluids_ml > MAX_SAFE_FLUIDS:
                debrief.append(
                    "Cuidado: administraste más fluidos de los necesarios; vigila signos de "
                    "sobrecarga (crepitantes, desaturación) en pacientes reales.")
            self.finish(True, "Paciente estabilizado",
                        "La TAM, frecuencia cardiaca y oxigenación se normalizaron y el foco "
                        "infeccioso está cubierto con antibiótico.", debrief)
            return

        if self.critical_s >= CRITICAL_HOLD_LIMIT:
            self.finish(False, "Shock refractario",
                        "La hipotensión mantenida (TAM < 50 mmHg) llevó a hipoperfusión "
                        "prolongada y paro cardiorrespiratorio.",
                        ["La TAM baja sostenida requiere iniciar vasopresor sin demora si los "
                         "fluidos no son suficientes.",
                         "No dejes pasar más de unos minutos con TAM crítica sin actuar."])
            return

        if self.overload_critical_s >= 40:
            self.finish(False, "Edema pulmonar por sobrecarga",
                        "El exceso de fluidos provocó edema agudo de pulmón e hipoxemia grave.",
                        ["Más de 3-4 litros de cristaloides sin reevaluar la respuesta puede "
                         "sobrecargar al paciente.",
                         "Si la TAM no responde a fluidos, es momento de iniciar vasopresor "
                         "en lugar de seguir con más líquidos."])
            return

        if s.time_s >= TIME_LIMIT:
            self.finish(False, "Tiempo agotado",
                        "No lograste estabilizar al paciente a tiempo.",
                        ["Actúa con rapidez: fluidos + vasopresor + antibiótico en los "
                         "primeros minutos mejoran el pronóstico del shock séptico."])
            return
