"""Escena principal de juego: monitor, panel de acciones y bitácora clínica."""
import pygame

from game.constants import (
    SCREEN_W, SCREEN_H, BLACK, WHITE, GREY, GREY_DARK, GREEN, CYAN, YELLOW,
    RED, PANEL_BG, SIM_TIME_SCALE,
)
from game.scenes.base import Scene
from game.ui.widgets import Button, Panel, draw_text, draw_wrapped
from game.ui.monitor import VitalsMonitor
from game.sim.cpr import CPRTracker

MONITOR_RECT = pygame.Rect(20, 60, 680, 250)
CPR_RECT = pygame.Rect(20, 320, 680, 46)
LOG_RECT = pygame.Rect(20, 376, 680, 140)
OBJ_RECT = pygame.Rect(20, 526, 680, 150)
PANEL_RECT = pygame.Rect(720, 60, 540, 640)


class GameplayScene(Scene):
    def __init__(self, app, case_cls):
        super().__init__(app)
        self.case = case_cls()
        self.monitor = VitalsMonitor()
        self.cpr_tracker = CPRTracker()
        self.widgets = self.case.create_widgets(PANEL_RECT)
        self.continue_btn = Button((SCREEN_W // 2 - 130, SCREEN_H - 130, 260, 50),
                                    "Ver resultados", self._go_results, size=22,
                                    color=(30, 90, 55))

    def _go_results(self):
        from game.scenes.results import ResultsScene
        self.app.change_scene(ResultsScene(self.app, self.case))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.cpr_tracker.press()
            elif event.key == pygame.K_ESCAPE:
                from game.scenes.case_select import CaseSelectScene
                self.app.change_scene(CaseSelectScene(self.app))
                return

        if self.case.finished:
            self.continue_btn.handle_event(event)
            return

        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt):
        dt_sim = dt * SIM_TIME_SCALE
        self.case.update(dt_sim, dt, self.cpr_tracker)
        self.monitor.update(dt_sim, self.case.state)

    def draw(self, surface):
        surface.fill(BLACK)
        s = self.case.state

        draw_text(surface, self.case.title, (20, 14), size=24, color=WHITE, bold=True)
        mins = int(s.time_s // 60)
        secs = int(s.time_s % 60)
        draw_text(surface, f"Tiempo: {mins:02d}:{secs:02d}", (SCREEN_W - 20, 14), size=18,
                   color=GREY, align_right=True)
        draw_text(surface, "ESC: volver a la seleccion de casos", (SCREEN_W - 20, 38), size=13,
                   color=GREY_DARK, align_right=True)

        self.monitor.draw(surface, MONITOR_RECT, s, alarm=self.case.alarm_active())

        self._draw_cpr_hud(surface)
        self._draw_log(surface)
        self._draw_objectives(surface)

        panel = Panel(PANEL_RECT, title="Acciones")
        panel.draw(surface)
        for w in self.widgets:
            w.draw(surface)

        if self.case.finished:
            self._draw_end_overlay(surface)

    def _draw_cpr_hud(self, surface):
        panel = Panel(CPR_RECT, bg=PANEL_BG)
        panel.draw(surface)
        if getattr(self.case, "phase", None) == "arrest":
            rate = self.cpr_tracker.rate_per_min()
            quality = self.cpr_tracker.quality()
            color = GREEN if quality > 0.8 else (YELLOW if quality > 0.3 else RED)
            draw_text(surface, "MANTEN PRESIONADA LA BARRA ESPACIADORA (100-120/min)",
                       (CPR_RECT.x + 12, CPR_RECT.y + 6), size=15, color=WHITE)
            draw_text(surface, f"{rate:.0f}/min", (CPR_RECT.right - 12, CPR_RECT.y + 6),
                       size=15, color=color, align_right=True)
            bar_rect = pygame.Rect(CPR_RECT.x + 12, CPR_RECT.y + 27, CPR_RECT.width - 24, 10)
            pygame.draw.rect(surface, GREY_DARK, bar_rect, border_radius=4)
            fill = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * quality), bar_rect.height)
            pygame.draw.rect(surface, color, fill, border_radius=4)
        else:
            draw_text(surface, "Sin necesidad de compresiones en este momento.",
                       (CPR_RECT.x + 12, CPR_RECT.y + 15), size=14, color=GREY)

    def _draw_log(self, surface):
        panel = Panel(LOG_RECT, title="Bitacora clinica")
        panel.draw(surface)
        y = LOG_RECT.y + 30
        for msg in self.case.state.log[-6:]:
            draw_text(surface, f"- {msg}", (LOG_RECT.x + 12, y), size=14, color=CYAN)
            y += 18

    def _draw_objectives(self, surface):
        panel = Panel(OBJ_RECT, title="Objetivos")
        panel.draw(surface)
        y = OBJ_RECT.y + 30
        for obj in self.case.objectives:
            y = draw_wrapped(surface, f"- {obj}", (OBJ_RECT.x + 12, y), 14,
                             OBJ_RECT.width - 24, color=WHITE, line_h=17) + 3

    def _draw_end_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        color = GREEN if self.case.won else RED
        draw_text(surface, self.case.end_title, (SCREEN_W // 2, SCREEN_H // 2 - 130), size=34,
                   color=color, bold=True, center=True)
        draw_wrapped(surface, self.case.end_message, (SCREEN_W // 2 - 340, SCREEN_H // 2 - 70),
                     18, 680, color=WHITE)
        self.continue_btn.draw(surface)
