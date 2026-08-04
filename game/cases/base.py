"""Interfaz común para los casos clínicos jugables."""


class BaseCase:
    case_id = "base"
    title = "Caso"
    subtitle = ""
    briefing = ""
    objectives = []
    difficulty = "*"
    time_limit_s = None  # límite de tiempo simulado (segundos) opcional

    def __init__(self):
        self.state = None
        self.finished = False
        self.won = False
        self.end_title = ""
        self.end_message = ""
        self.debrief = []
        self.elapsed_stable_s = 0.0

    def create_widgets(self, panel_rect):
        """Devuelve una lista de widgets (Button/Slider/Toggle) para el panel de acciones."""
        return []

    def update(self, dt_sim, dt_real, cpr_tracker=None):
        """Avanza la fisiología. dt_sim = segundos de paciente simulados en este frame."""
        raise NotImplementedError

    def alarm_active(self):
        from game.sim.patient import vitals_alarm
        return vitals_alarm(self.state)

    def finish(self, won, title, message, debrief):
        self.finished = True
        self.won = won
        self.end_title = title
        self.end_message = message
        self.debrief = debrief

    def stars(self):
        if not self.won:
            return 0
        score = self.state.total_score
        if score >= 90:
            return 3
        if score >= 60:
            return 2
        return 1
