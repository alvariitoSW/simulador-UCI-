"""Pantalla de título del juego."""
import pygame

from game.constants import SCREEN_W, SCREEN_H, BLACK, WHITE, GREY, GREEN, CYAN
from game.scenes.base import Scene
from game.ui.widgets import Button, draw_text, draw_wrapped
from game.ui.monitor import VitalsMonitor
from game.sim.patient import PatientState


class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.monitor = VitalsMonitor(num_samples=260)
        self.preview_state = PatientState(hr=78, sbp=118, dbp=74, spo2=98, rr=15)

        cx = SCREEN_W // 2
        self.buttons = [
            Button((cx - 140, 470, 280, 54), "Jugar", self._play, size=26,
                   color=(30, 90, 55)),
            Button((cx - 140, 540, 280, 46), "Salir", self._quit, size=22),
        ]

    def _play(self):
        from game.scenes.case_select import CaseSelectScene
        self.app.change_scene(CaseSelectScene(self.app))

    def _quit(self):
        self.app.running = False

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        self.monitor.update(dt * 1.0, self.preview_state)

    def draw(self, surface):
        surface.fill(BLACK)
        draw_text(surface, "SIMULADOR UCI", (SCREEN_W // 2, 130), size=56, color=WHITE,
                   bold=True, center=True)
        draw_text(surface, "Aprende cuidados intensivos jugando", (SCREEN_W // 2, 185),
                   size=22, color=CYAN, center=True)

        mon_rect = pygame.Rect(SCREEN_W // 2 - 320, 230, 640, 200)
        self.monitor.draw(surface, mon_rect, self.preview_state, alarm=False)

        for b in self.buttons:
            b.draw(surface)

        draw_wrapped(surface, "Proyecto educativo sin validez clinica real. No sustituye la "
                     "formacion ni los protocolos oficiales.", (SCREEN_W // 2 - 260, 615), 15,
                     520, color=GREY)
        draw_text(surface, "Un juego indie para estudiar mientras juegas.",
                   (SCREEN_W // 2, 660), size=15, color=GREY, center=True)
