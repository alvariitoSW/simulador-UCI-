"""Pantalla de resultados y retroalimentación educativa al terminar un caso."""
import pygame

from game.constants import SCREEN_W, SCREEN_H, BLACK, WHITE, GREY, GREEN, RED, YELLOW, CYAN
from game.scenes.base import Scene
from game.ui.widgets import Button, Panel, draw_text, draw_wrapped
from game import progress


class ResultsScene(Scene):
    def __init__(self, app, case):
        super().__init__(app)
        self.case = case
        self.score = case.state.total_score
        self.stars = case.stars()
        progress.record_result(case.case_id, self.score, self.stars, case.won)

        cx = SCREEN_W // 2
        self.buttons = [
            Button((cx - 330, SCREEN_H - 90, 200, 48), "Reintentar", self._retry, size=18),
            Button((cx - 110, SCREEN_H - 90, 220, 48), "Elegir otro caso", self._select,
                   size=18, color=(30, 90, 55)),
            Button((cx + 130, SCREEN_H - 90, 200, 48), "Menu principal", self._menu, size=18),
        ]

    def _retry(self):
        from game.scenes.gameplay import GameplayScene
        self.app.change_scene(GameplayScene(self.app, type(self.case)))

    def _select(self):
        from game.scenes.case_select import CaseSelectScene
        self.app.change_scene(CaseSelectScene(self.app))

    def _menu(self):
        from game.scenes.menu import MenuScene
        self.app.change_scene(MenuScene(self.app))

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(BLACK)
        color = GREEN if self.case.won else RED
        draw_text(surface, self.case.end_title, (SCREEN_W // 2, 60), size=36, color=color,
                   bold=True, center=True)
        draw_wrapped(surface, self.case.end_message, (SCREEN_W // 2 - 420, 110), 18, 840,
                     color=WHITE)

        draw_text(surface, f"Puntuacion: {self.score}", (SCREEN_W // 2 - 420, 170), size=20,
                   color=CYAN)
        star_str = "*" * self.stars + "." * (3 - self.stars)
        draw_text(surface, f"Estrellas: {star_str}", (SCREEN_W // 2 + 250, 170), size=20,
                   color=YELLOW, align_right=True)

        debrief_rect = pygame.Rect(SCREEN_W // 2 - 420, 210, 840, 250)
        panel = Panel(debrief_rect, title="Puntos clave para estudiar")
        panel.draw(surface)
        y = debrief_rect.y + 34
        for point in self.case.debrief:
            y = draw_wrapped(surface, f"- {point}", (debrief_rect.x + 16, y), 16,
                             debrief_rect.width - 32, color=WHITE, line_h=19) + 8

        events_rect = pygame.Rect(SCREEN_W // 2 - 420, 475, 840, 130)
        panel2 = Panel(events_rect, title="Eventos de puntuacion")
        panel2.draw(surface)
        y = events_rect.y + 30
        for ev in self.case.state.score_events[-5:]:
            sign = "+" if ev["points"] >= 0 else ""
            draw_text(surface, f"{sign}{ev['points']}  {ev['reason']}", (events_rect.x + 16, y),
                       size=15, color=GREY)
            y += 20

        for b in self.buttons:
            b.draw(surface)
