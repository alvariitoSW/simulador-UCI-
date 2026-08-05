"""Caso 5: Neutropenia febril de alto riesgo (hemato-oncologia).

Basado en la guia de consenso SEIMC-SEHH 2020 sobre neutropenia febril: el
riesgo se estratifica primero por "red flags" (que invalidan el indice
MASCC si estan presentes) y el pilar del tratamiento es hemocultivos +
antibiotico empirico de amplio espectro sin demora.
"""
from game.cases.base import BaseCase
from game.sim.patient import PatientState, clamp, approach
from game.ui.widgets import Button, Slider, Toggle

TIME_LIMIT = 480.0
STABLE_HOLD_REQUIRED = 40.0
CRITICAL_HOLD_LIMIT = 100.0
MAX_SAFE_FLUIDS = 3000.0
ABX_FAST_WINDOW = 60.0  # "puerta-antibiotico" objetivo en segundos simulados


class NeutropeniaCase(BaseCase):
    case_id = "neutropenia_febril"
    title = "Neutropenia febril de alto riesgo"
    subtitle = "Paciente con LMA en induccion, fiebre y neutropenia grave"
    difficulty = "***"
    briefing = (
        "Paciente en induccion para leucemia mieloide aguda (LMA), neutropenia "
        "grave (ANC 80/mm3), que en las ultimas horas presenta fiebre de 39.1C, "
        "taquicardia e hipotension limite, con leve eritema en el punto de "
        "insercion del cateter venoso central. Reconoce los signos de alarma, "
        "extrae cultivos y no demores el antibiotico empirico."
    )
    objectives = [
        "Identificar los criterios de alto riesgo (\"red flags\") que invalidan el MASCC",
        "Extraer hemocultivos (perifericos + cateter) antes o junto al antibiotico",
        "Iniciar antibiotico empirico de amplio espectro sin demora (<1h)",
        "Valorar la retirada del cateter venoso central si hay sospecha de foco",
        "Reanimar con fluidos/vasopresor y mantener TAM >= 65 mmHg",
    ]
    time_limit_s = TIME_LIMIT

    def __init__(self):
        super().__init__()
        self.state = PatientState(
            name="Paciente E - Neutropenia febril", age=44, weight_kg=68,
            hr=124, sbp=86, dbp=50, spo2=95, rr=24, temp=39.1, lactate=3.1,
            rhythm="sinusal",
        )
        self.state.anc = 80
        self.state.add_log("LMA en induccion. ANC 80/mm3. Fiebre 39.1C, TA limite.")

        self.flags_true = {"sepsis": True, "lma": True, "idsa": False}
        self.flags_checked = {"sepsis": False, "lma": False, "idsa": False}
        self._flags_bonus_given = False
        self.cultures_drawn = False
        self.catheter_removed = False
        self._abx_bonus_given = False
        self.critical_s = 0.0
        self._abx_btn = None

    # ---------------- UI ----------------
    def create_widgets(self, panel_rect):
        widgets = []
        x = panel_rect.x + 16
        w = panel_rect.width - 32
        y = panel_rect.y + 40

        def make_toggle(key, label):
            def _toggle():
                self.flags_checked[key] = not self.flags_checked[key]
                self._evaluate_flags()
            return Toggle((x, y, w, 34), label, lambda k=key: self.flags_checked[k],
                          _toggle, size=15)

        widgets.append(make_toggle("sepsis", "Red flag: sepsis / shock"))
        y += 46
        widgets.append(make_toggle("lma", "Red flag: LMA en fase critica (induccion)"))
        y += 46
        widgets.append(make_toggle("idsa", "Red flag: comorbilidad IDSA alto riesgo"))
        y += 46

        def draw_cultures():
            if not self.cultures_drawn:
                self.cultures_drawn = True
                self.state.add_log("Hemocultivos extraidos (perifericos + cateter).")
                self.state.score(10, "Hemocultivos antes/junto al antibiotico")

        widgets.append(Button((x, y, w, 36), "Extraer hemocultivos (x2)", draw_cultures,
                               size=16))
        y += 52

        def remove_catheter():
            if not self.catheter_removed:
                self.catheter_removed = True
                self.state.add_log("Cateter venoso central retirado (sospecha de foco).")
                self.state.score(10, "Manejo del foco de cateter")

        widgets.append(Button((x, y, w, 36), "Retirar cateter venoso central",
                               remove_catheter, size=16))
        y += 52

        def give_abx():
            if not self.state.antibiotics_given:
                self.state.antibiotics_given = True
                self.state.add_log("Antibiotico empirico iniciado: carbapenem (meropenem).")
                if not self._abx_bonus_given and self.state.time_s < ABX_FAST_WINDOW:
                    self.state.score(25, "Antibiotico empirico precoz (<1h)")
                    self._abx_bonus_given = True

        abx_btn = Button((x, y, w, 40), "Antibiotico empirico: carbapenem", give_abx)
        widgets.append(abx_btn)
        self._abx_btn = abx_btn
        y += 56

        def give_fluids():
            self.state.fluids_ml += 500
            self.state.add_log(f"Bolo de 500 ml administrado (total {self.state.fluids_ml:.0f} ml).")

        widgets.append(Button((x, y, w, 40), "Bolo de cristaloides (+500 ml)", give_fluids))
        y += 56

        def set_norepi(v):
            self.state.vasopressor_mcgkgmin = v

        widgets.append(Slider((x, y + 20, w, 14), 0.0, 1.0, self.state.vasopressor_mcgkgmin,
                               step=0.02, label="Noradrenalina", unit="mcg/kg/min",
                               fmt="{:.2f}", on_change=set_norepi))
        return widgets

    def _evaluate_flags(self):
        all_true_checked = all(self.flags_checked[k] for k, v in self.flags_true.items() if v)
        if all_true_checked and not self._flags_bonus_given:
            self._flags_bonus_given = True
            self.state.add_log(
                "Red flags reconocidos: riesgo ALTO automatico, el indice MASCC queda "
                "invalidado. Ingreso + antibiotico IV sin demora.")
            self.state.score(15, "Red flags reconocidos correctamente")

    def status_lines(self):
        risk = "ALTO (red flags activos)" if self._flags_bonus_given else "pendiente de evaluar"
        return [
            f"Neutrofilos (ANC): {self.state.anc:.0f}/mm3 (neutropenia grave)",
            f"Categoria de riesgo: {risk}",
            f"Cultivos: {'extraidos' if self.cultures_drawn else 'pendientes'}"
            f" | ATB: {'iniciado' if self.state.antibiotics_given else 'pendiente'}",
        ]

    # ---------------- Fisiologia ----------------
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

        target_map = clamp(53.0 + fluid_effect + vaso_effect - overload_penalty * 0.3, 32.0, 100.0)
        target_sbp = target_map + 25.0
        target_dbp = target_map - 15.0
        s.sbp = approach(s.sbp, target_sbp, 0.05, dt_sim)
        s.dbp = approach(s.dbp, target_dbp, 0.05, dt_sim)

        target_hr = clamp(150.0 - (target_map - 55.0) * 4.2 + overload_penalty * 1.4, 68.0, 165.0)
        s.hr = approach(s.hr, target_hr, 0.04, dt_sim)

        target_spo2 = clamp(96.0 - overload_penalty * 1.1, 78.0, 99.0)
        s.spo2 = approach(s.spo2, target_spo2, 0.03, dt_sim)

        target_rr = clamp(24.0 - (target_map - 55.0) * 0.06 + overload_penalty * 0.9
                           + max(0.0, 94.0 - s.spo2) * 0.3, 14.0, 40.0)
        s.rr = approach(s.rr, target_rr, 0.05, dt_sim)

        if s.antibiotics_given:
            s.temp = approach(s.temp, 37.0, 0.008, dt_sim)
        else:
            s.temp = clamp(s.temp + dt_sim * 0.0015, 36.5, 40.8)

        if s.antibiotics_given and s.map >= 65:
            s.lactate = approach(s.lactate, 0.9, 0.008, dt_sim)
        elif s.map < 50:
            s.lactate = clamp(s.lactate + dt_sim * 0.012, 0.5, 12.0)

        if s.map < 50:
            self.critical_s += dt_sim
        else:
            self.critical_s = max(0.0, self.critical_s - dt_sim * 0.5)

        stable = (s.map >= 65 and s.hr < 110 and s.spo2 >= 92 and s.antibiotics_given
                  and self.cultures_drawn and self._flags_bonus_given and s.lactate < 2.5)
        if stable:
            self.elapsed_stable_s += dt_sim
        else:
            self.elapsed_stable_s = max(0.0, self.elapsed_stable_s - dt_sim)

        if self.elapsed_stable_s >= STABLE_HOLD_REQUIRED:
            time_bonus = max(0, (TIME_LIMIT - s.time_s) / TIME_LIMIT * 25)
            s.score(35, "Paciente neutropenico estabilizado")
            s.score(round(time_bonus), "Bonificacion por rapidez")
            debrief = [
                "Cuando hay red flags (sepsis/shock, LMA en fase critica, comorbilidad "
                "IDSA de alto riesgo), el indice MASCC queda invalidado: es alto riesgo "
                "automatico, sin necesidad de calcular la puntuacion.",
                "El pilar del tratamiento es hemocultivos + antibiotico empirico de "
                "amplio espectro sin demora (idealmente <1h desde la fiebre).",
                "En paciente inestable, el antibiotico de eleccion es un carbapenem, "
                "solo o combinado con aminoglucosido hasta descartar bacteriemia.",
                "Fuente: Documento de consenso SEIMC-SEHH 2020 sobre el manejo de la "
                "neutropenia febril en el paciente hemato-oncologico.",
            ]
            if self.catheter_removed:
                debrief.append(
                    "Retiraste el cateter ante la sospecha de infeccion asociada: "
                    "correcto cuando hay signos locales o inestabilidad sin otro foco claro.")
            self.finish(True, "Neutropenia febril controlada",
                        "Reconociste el alto riesgo, cubriste el foco con antibiotico "
                        "precoz y mantuviste una hemodinamica estable.", debrief)
            return

        if self.critical_s >= CRITICAL_HOLD_LIMIT:
            self.finish(False, "Shock septico refractario",
                        "La hipotension mantenida en un paciente neutropenico llevo a "
                        "hipoperfusion prolongada y deterioro irreversible.",
                        ["En el paciente neutropenico febril inestable, cada minuto sin "
                         "antibiotico de amplio espectro aumenta la mortalidad.",
                         "No esperes a completar el estudio diagnostico para iniciar el "
                         "tratamiento empirico."])
            return

        if s.time_s >= TIME_LIMIT:
            self.finish(False, "Tiempo agotado",
                        "No lograste estabilizar ni cubrir el foco a tiempo.",
                        ["La guia SEIMC-SEHH 2020 recomienda antibiotico empirico en "
                         "menos de 1 hora desde la fiebre en el paciente de alto riesgo.",
                         "Reconoce las red flags cuanto antes: invalidan el MASCC y "
                         "marcan el ingreso y el antibiotico IV inmediato."])
            return
