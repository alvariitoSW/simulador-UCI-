"""Aplicación principal: crea la ventana y gestiona el bucle de juego y las escenas."""
import asyncio
import sys

import pygame

from game.constants import SCREEN_W, SCREEN_H, FPS, TITLE


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True

        # Importación diferida para evitar ciclos de import.
        from game.scenes.menu import MenuScene
        self.scene = MenuScene(self)

    def change_scene(self, scene):
        self.scene = scene

    async def run_async(self):
        """Bucle principal asíncrono, compatible con pygbag (compilación a web/WASM)."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # evita saltos grandes si la ventana se congela

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

            # Cede el control al navegador en la build web; en escritorio no tiene coste real.
            await asyncio.sleep(0)

        pygame.quit()
        if sys.platform != "emscripten":
            sys.exit(0)

    def run(self):
        asyncio.run(self.run_async())
