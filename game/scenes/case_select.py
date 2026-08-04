"""Pantalla de selección de caso clínico."""
import pygame

from game.constants import SCREEN_W, SCREEN_H, BLACK, WHITE, GREY, GREY_DARK, CYAN, YELLOW
from game.scenes.base import Scene
from game.ui.widgets import Button, Panel, draw_text, draw_wrapped
from game.cases.registry import CASES
from game import progress


class CaseSelectScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.progress = progress.load()
        self.buttons = []
        self.cards = []

        top = 130
        card_h = 110
        gap = 16
        card_w = SCREEN_W - 240
        x = 120

        for i, case_cls in enumerate(CASES):
            y = top + i * (card_h + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            self.cards.append((case_cls, rect))
            btn = Button((rect.right - 150, rect.y + card_h // 2 - 22, 120, 44), "Jugar",
                         self._make_play(case_cls), color=(30, 90, 55))
            self.buttons.append(btn)

        self.back_btn = Button((40, SCREEN_H - 70, 140, 44), "Volver", self._back)

    def _make_play(self, case_cls):
        def _play():
            from game.scenes.gameplay import GameplayScene
            self.app.change_scene(GameplayScene(self.app, case_cls))
        return _play

    def _back(self):
        from game.scenes.menu import MenuScene
        self.app.change_scene(MenuScene(self.app))

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)
        self.back_btn.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(BLACK)
        draw_text(surface, "Selecciona un caso clinico", (SCREEN_W // 2, 60), size=36,
                   color=WHITE, bold=True, center=True)

        for (case_cls, rect), btn in zip(self.cards, self.buttons):
            panel = Panel(rect)
            panel.draw(surface)
            draw_text(surface, case_cls.title, (rect.x + 20, rect.y + 14), size=22, color=WHITE,
                       bold=True)
            draw_text(surface, case_cls.difficulty, (rect.right - 170, rect.y + 16), size=16,
                       color=YELLOW)
            draw_wrapped(surface, case_cls.subtitle, (rect.x + 20, rect.y + 46), 16,
                         rect.width - 210, color=GREY)

            stars = self.progress.get("stars", {}).get(case_cls.case_id, 0)
            star_str = "*" * stars + "." * (3 - stars)
            draw_text(surface, f"Mejor resultado: {star_str}", (rect.x + 20, rect.y + 80),
                       size=14, color=CYAN)

            btn.draw(surface)

        self.back_btn.draw(surface)
