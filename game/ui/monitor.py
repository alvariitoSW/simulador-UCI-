"""Monitor de signos vitales estilo UCI: ondas de ECG, pletismografía (SpO2) y respiración."""
import math
import random

import pygame

from game.constants import BLACK, GREEN, CYAN, YELLOW, WHITE, RED, GREY_DARK, ORANGE
from game.ui.widgets import draw_text

SHOCKABLE_RHYTHMS = ("fv", "tvsp")
FLATLINE_RHYTHMS = ("asistolia",)
RHYTHM_NAMES = {
    "sinusal": "RITMO SINUSAL",
    "fv": "FIBRILACION VENTRICULAR",
    "tvsp": "TV SIN PULSO",
    "asistolia": "ASISTOLIA",
    "aesp": "AESP",
}


def _interp_template(points, phase):
    """Interpola linealmente entre puntos (fase 0..1, valor) y envuelve al final."""
    if phase <= points[0][0]:
        return points[0][1]
    if phase >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= phase <= x1:
            if x1 == x0:
                return y0
            t = (phase - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return 0.0


ECG_POINTS = [
    (0.00, 0.0), (0.08, 0.0), (0.12, 0.10), (0.16, 0.0), (0.20, 0.0),
    (0.22, -0.15), (0.24, 1.0), (0.26, -0.30), (0.28, 0.0), (0.40, 0.0),
    (0.46, 0.25), (0.55, 0.0), (1.00, 0.0),
]

PLETH_POINTS = [
    (0.00, 0.0), (0.05, 0.0), (0.15, 1.0), (0.30, 0.55), (0.38, 0.65),
    (0.55, 0.20), (0.80, 0.0), (1.00, 0.0),
]


class VitalsMonitor:
    def __init__(self, num_samples=320):
        self.num_samples = num_samples
        self.ecg_buf = [0.0] * num_samples
        self.pleth_buf = [0.0] * num_samples
        self.resp_buf = [0.0] * num_samples
        self.ecg_t = 0.0
        self.pleth_t = 0.0
        self.resp_t = 0.0
        self.sample_accum = 0.0
        self.samples_per_sec = 45

    def update(self, sim_dt, state):
        self.sample_accum += sim_dt
        step = 1.0 / self.samples_per_sec
        guard = 0
        while self.sample_accum >= step and guard < 200:
            self.sample_accum -= step
            self.ecg_t += step
            self.pleth_t += step
            self.resp_t += step
            self._push_sample(state, step)
            guard += 1

    def _push_sample(self, state, step):
        hr = max(state.hr, 1)
        rhythm = getattr(state, "rhythm", "sinusal")

        if rhythm in FLATLINE_RHYTHMS:
            ecg_v = random.uniform(-0.02, 0.02)
        elif rhythm in SHOCKABLE_RHYTHMS:
            ecg_v = random.uniform(-1, 1) * 0.85
        else:
            period = 60.0 / hr
            phase = (self.ecg_t % period) / period
            ecg_v = _interp_template(ECG_POINTS, phase)
        self.ecg_buf.append(ecg_v)
        self.ecg_buf.pop(0)

        no_pulse = rhythm in FLATLINE_RHYTHMS or rhythm in SHOCKABLE_RHYTHMS
        if no_pulse or state.spo2 <= 0:
            pleth_v = 0.0
        else:
            period = 60.0 / hr
            phase = (self.pleth_t % period) / period
            amp = max(0.15, min(1.0, state.spo2 / 100.0))
            pleth_v = _interp_template(PLETH_POINTS, phase) * amp
        self.pleth_buf.append(pleth_v)
        self.pleth_buf.pop(0)

        rr = max(state.rr, 1)
        if getattr(state, "apnea", False):
            resp_v = 0.0
        else:
            period = 60.0 / rr
            phase = (self.resp_t % period) / period
            resp_v = math.sin(phase * 2 * math.pi) * 0.8
        self.resp_buf.append(resp_v)
        self.resp_buf.pop(0)

    def _draw_wave(self, surface, rect, buf, color):
        pygame.draw.rect(surface, (0, 0, 0), rect)
        n = len(buf)
        if n < 2:
            return
        step_x = rect.width / (n - 1)
        mid_y = rect.y + rect.height / 2
        amp = rect.height / 2 - 4
        points = []
        for i, v in enumerate(buf):
            x = rect.x + i * step_x
            y = mid_y - v * amp
            points.append((x, y))
        pygame.draw.lines(surface, color, False, points, 2)

    def draw(self, surface, rect, state, alarm=False):
        pygame.draw.rect(surface, (0, 0, 0), rect, border_radius=6)
        border_color = RED if (alarm and (pygame.time.get_ticks() // 400) % 2 == 0) else GREY_DARK
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=6)

        wave_w = int(rect.width * 0.68)
        wave_area = pygame.Rect(rect.x + 8, rect.y + 8, wave_w - 16, rect.height - 16)
        h3 = wave_area.height // 3
        ecg_rect = pygame.Rect(wave_area.x, wave_area.y, wave_area.width, h3 - 4)
        pleth_rect = pygame.Rect(wave_area.x, wave_area.y + h3, wave_area.width, h3 - 4)
        resp_rect = pygame.Rect(wave_area.x, wave_area.y + 2 * h3, wave_area.width, h3 - 4)

        self._draw_wave(surface, ecg_rect, self.ecg_buf, GREEN)
        self._draw_wave(surface, pleth_rect, self.pleth_buf, CYAN)
        self._draw_wave(surface, resp_rect, self.resp_buf, YELLOW)

        draw_text(surface, "ECG", (ecg_rect.x + 4, ecg_rect.y + 2), size=12, color=GREEN)
        rhythm_label = RHYTHM_NAMES.get(getattr(state, "rhythm", ""), state.rhythm)
        rhythm_color = RED if getattr(state, "rhythm", "") in (SHOCKABLE_RHYTHMS + FLATLINE_RHYTHMS) else GREEN
        draw_text(surface, rhythm_label, (ecg_rect.right - 4, ecg_rect.y + 2), size=12,
                   color=rhythm_color, align_right=True)
        draw_text(surface, "SpO2", (pleth_rect.x + 4, pleth_rect.y + 2), size=12, color=CYAN)
        draw_text(surface, "RESP", (resp_rect.x + 4, resp_rect.y + 2), size=12, color=YELLOW)

        num_rect = pygame.Rect(rect.x + wave_w, rect.y, rect.width - wave_w, rect.height)
        self._draw_numbers(surface, num_rect, state)

    def _draw_numbers(self, surface, rect, state):
        pygame.draw.line(surface, GREY_DARK, (rect.x, rect.y + 6), (rect.x, rect.bottom - 6), 1)
        pad = 10
        x = rect.x + pad
        w = rect.width - 2 * pad

        def row(y, label, value, unit, color, size=30):
            draw_text(surface, label, (x, y), size=12, color=color)
            draw_text(surface, value, (x, y + 13), size=size, color=color, bold=True)
            draw_text(surface, unit, (x + w, y + size - 6), size=12, color=color, align_right=True)

        no_pulse = getattr(state, "rhythm", "") in FLATLINE_RHYTHMS + SHOCKABLE_RHYTHMS
        hr_val = "---" if no_pulse else f"{state.hr:.0f}"
        row(rect.y + 6, "FC (lpm)", hr_val, "bpm", GREEN)
        bp_val = "--/--" if no_pulse else f"{state.sbp:.0f}/{state.dbp:.0f}"
        map_val = "(--)" if no_pulse else f"({state.map:.0f})"
        row(rect.y + 66, "TA (mmHg)", bp_val, map_val, RED)
        row(rect.y + 126, "SpO2 (%)", f"{state.spo2:.0f}", "%", CYAN)
        row(rect.y + 186, "FR (rpm)", f"{state.rr:.0f}", "rpm", YELLOW)
        row(rect.y + 246, "Temp (C)", f"{state.temp:.1f}", "C", ORANGE, size=22)
