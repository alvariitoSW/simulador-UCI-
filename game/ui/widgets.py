"""Widgets de UI reutilizables: botones, sliders, paneles y helpers de texto."""
import pygame

from game.constants import (
    WHITE, GREY, GREY_DARK, PANEL_BG, PANEL_BG_LIGHT, GREEN, GREEN_DARK,
    CYAN, RED,
)

_font_cache = {}


def get_font(size, bold=False):
    # Se usa la fuente integrada de Pygame (pygame.font.Font(None, ...)) en vez de
    # pygame.font.SysFont: esta última busca fuentes instaladas en el sistema operativo,
    # algo que no existe al compilar a WebAssembly con pygbag, y ahi rompe el arranque.
    key = (size, bold)
    if key not in _font_cache:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _font_cache[key] = f
    return _font_cache[key]


def draw_text(surface, text, pos, size=20, color=WHITE, bold=False, center=False,
              align_right=False):
    font = get_font(size, bold)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    elif align_right:
        rect.topright = pos
    else:
        rect.topleft = pos
    surface.blit(img, rect)
    return rect


def wrap_text(text, size, max_width, bold=False):
    font = get_font(size, bold)
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(surface, text, pos, size, max_width, color=WHITE, line_h=None, bold=False):
    lines = wrap_text(text, size, max_width, bold)
    line_h = line_h or (size + 6)
    x, y = pos
    for i, line in enumerate(lines):
        draw_text(surface, line, (x, y + i * line_h), size=size, color=color, bold=bold)
    return y + len(lines) * line_h


class Button:
    def __init__(self, rect, label, callback=None, color=PANEL_BG_LIGHT,
                 hover_color=None, text_color=WHITE, size=20, enabled=True,
                 border_color=GREY_DARK):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.callback = callback
        self.color = color
        self.hover_color = hover_color or tuple(min(255, c + 25) for c in color)
        self.text_color = text_color
        self.size = size
        self.enabled = enabled
        self.border_color = border_color
        self.hovered = False

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface):
        color = self.color if self.enabled else GREY_DARK
        if self.enabled and self.hovered:
            color = self.hover_color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, self.border_color, self.rect, width=1, border_radius=6)
        text_color = self.text_color if self.enabled else GREY
        draw_text(surface, self.label, self.rect.center, size=self.size,
                   color=text_color, center=True)


class Toggle(Button):
    """Botón que conmuta un estado booleano y cambia de color cuando está activo."""

    def __init__(self, rect, label, get_state, on_toggle, size=18):
        super().__init__(rect, label, callback=on_toggle, size=size)
        self.get_state = get_state

    def draw(self, surface):
        active = self.get_state()
        color = GREEN_DARK if active else PANEL_BG_LIGHT
        if self.hovered:
            color = tuple(min(255, c + 25) for c in color)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        border = GREEN if active else GREY_DARK
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=6)
        draw_text(surface, self.label, self.rect.center, size=self.size,
                   color=WHITE, center=True)


class Slider:
    def __init__(self, rect, min_v, max_v, value, step=1, label="", unit="",
                 fmt="{:.0f}", on_change=None, color=CYAN, enabled=True):
        self.rect = pygame.Rect(rect)
        self.min_v = min_v
        self.max_v = max_v
        self.value = value
        self.step = step
        self.label = label
        self.unit = unit
        self.fmt = fmt
        self.on_change = on_change
        self.color = color
        self.dragging = False
        self.enabled = enabled

    def _set_from_mouse(self, mx):
        t = (mx - self.rect.x) / max(1, self.rect.width)
        t = max(0.0, min(1.0, t))
        raw = self.min_v + t * (self.max_v - self.min_v)
        steps = round((raw - self.min_v) / self.step)
        self.value = self.min_v + steps * self.step
        self.value = max(self.min_v, min(self.max_v, self.value))
        if self.on_change:
            self.on_change(self.value)

    def handle_event(self, event):
        if not self.enabled:
            return False
        handle_rect = self._handle_rect()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self._set_from_mouse(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0])
            return True
        return False

    def _handle_rect(self):
        t = (self.value - self.min_v) / max(1e-9, (self.max_v - self.min_v))
        hx = self.rect.x + int(t * self.rect.width)
        return pygame.Rect(hx - 6, self.rect.y - 5, 12, self.rect.height + 10)

    def draw(self, surface):
        label_txt = f"{self.label}: {self.fmt.format(self.value)} {self.unit}".strip()
        label_color = WHITE if self.enabled else GREY
        draw_text(surface, label_txt, (self.rect.x, self.rect.y - 20), size=16, color=label_color)
        pygame.draw.rect(surface, GREY_DARK, self.rect, border_radius=4)
        if not self.enabled:
            pygame.draw.rect(surface, GREY, self.rect, width=1, border_radius=4)
            return
        t = (self.value - self.min_v) / max(1e-9, (self.max_v - self.min_v))
        fill_w = int(t * self.rect.width)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(surface, self.color, fill_rect, border_radius=4)
        pygame.draw.rect(surface, GREY, self.rect, width=1, border_radius=4)
        pygame.draw.rect(surface, WHITE, self._handle_rect(), border_radius=3)


class Panel:
    def __init__(self, rect, title=None, bg=PANEL_BG, border=GREY_DARK):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.bg = bg
        self.border = border

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, self.border, self.rect, width=1, border_radius=8)
        if self.title:
            draw_text(surface, self.title, (self.rect.x + 12, self.rect.y + 8),
                       size=16, color=GREY, bold=True)
