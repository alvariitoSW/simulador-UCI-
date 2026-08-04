"""Mecánica de RCP (compresiones torácicas) y desfibrilación."""
import random

import pygame

from game.sim.patient import clamp

COMPRESSION_WINDOW_MS = 8000
RECENCY_MS = 1500


class CPRTracker:
    """Rastrea las pulsaciones de la barra espaciadora para simular compresiones torácicas."""

    def __init__(self):
        self.press_times = []

    def press(self):
        now = pygame.time.get_ticks()
        self.press_times.append(now)
        self._trim(now)

    def _trim(self, now):
        self.press_times = [t for t in self.press_times if now - t <= COMPRESSION_WINDOW_MS]

    def rate_per_min(self):
        now = pygame.time.get_ticks()
        self._trim(now)
        if len(self.press_times) < 2:
            return 0.0
        span = (self.press_times[-1] - self.press_times[0]) / 1000.0
        if span <= 0:
            return 0.0
        return (len(self.press_times) - 1) / span * 60.0

    def is_compressing(self):
        now = pygame.time.get_ticks()
        return bool(self.press_times) and (now - self.press_times[-1] <= RECENCY_MS)

    def quality(self):
        """Calidad de la RCP en curso, de 0.0 a 1.0. El objetivo ACLS es 100-120/min."""
        if not self.is_compressing():
            return 0.0
        r = self.rate_per_min()
        if r <= 0:
            return 0.0
        if 100 <= r <= 120:
            return 1.0
        if r < 100:
            return clamp(r / 100.0, 0.0, 1.0)
        return clamp(1.0 - (r - 120) / 80.0, 0.0, 1.0)


def shock_conversion_chance(time_in_arrest_s, cpr_quality_avg):
    """Probabilidad de que una descarga convierta un ritmo desfibrilable a ritmo sinusal."""
    base = 0.55
    base -= min(0.35, time_in_arrest_s / 240.0 * 0.35)
    base += cpr_quality_avg * 0.25
    return clamp(base, 0.05, 0.9)


def attempt_shock(time_in_arrest_s, cpr_quality_avg):
    chance = shock_conversion_chance(time_in_arrest_s, cpr_quality_avg)
    return random.random() < chance
