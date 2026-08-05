"""Pantalla de selección de caso clínico."""
import pygame

from game.constants import SCREEN_W, SCREEN_H, BLACK, WHITE, GREY, GREY_DARK, CYAN, YELLOW
from game.scenes.base import Scene
from game.ui.widgets import Button, Panel, draw_text, draw_wrapped
from game.cases.registry import CASES
from game import progress

TOP = 100
BOTTOM = SCREEN_H - 90
GAP = 12
MAX_CARD_H = 110
MIN_CARD_H = 66


class CaseSelectScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.progress = progress.load()
        self.buttons = []
        self.cards = []

        n = len(CASES)
        available = BOTTOM - TOP - GAP * (n - 1)
        card_h = max(MIN_CARD_H, min(MAX_CARD_H, available / n))
        card_w = SCREEN_W - 240
        x = 120
        btn_h = min(44, card_h - 20)

        for i, case_cls in enumerate(CASES):
            y = TOP + i * (card_h + GAP)
            rect = pygame.Rect(x, round(y), card_w, round(card_h))
            self.cards.append((case_cls, rect))
            btn = Button((rect.right - 150, rect.centery - btn_h // 2, 120, btn_h), "Jugar",
                         self._make_play(case_cls), color=(30, 90, 55))
            self.buttons.append(btn)

        self.card_h = card_h
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
        draw_text(surface, "Selecciona un caso clinico", (SCREEN_W // 2, 40), size=32,
                   color=WHITE, bold=True, center=True)

        compact = self.card_h < 90
        title_size = 18 if compact else 22
        sub_size = 14 if compact else 16

        for (case_cls, rect), btn in zip(self.cards, self.buttons):
            panel = Panel(rect)
            panel.draw(surface)
            draw_text(surface, case_cls.title, (rect.x + 18, rect.y + rect.height * 0.12),
                       size=title_size, color=WHITE, bold=True)
            draw_text(surface, case_cls.difficulty, (rect.right - 170, rect.y + rect.height * 0.14),
                       size=14, color=YELLOW)
            draw_wrapped(surface, case_cls.subtitle, (rect.x + 18, rect.y + rect.height * 0.42),
                         sub_size, rect.width - 210, color=GREY, line_h=sub_size + 3)

            if not compact:
                stars = self.progress.get("stars", {}).get(case_cls.case_id, 0)
                star_str = "*" * stars + "." * (3 - stars)
                draw_text(surface, f"Mejor resultado: {star_str}",
                           (rect.x + 18, rect.y + rect.height * 0.75), size=13, color=CYAN)

            btn.draw(surface)

        self.back_btn.draw(surface)
