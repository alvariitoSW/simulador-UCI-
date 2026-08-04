#!/usr/bin/env python3
"""Simulador UCI - punto de entrada del juego.

Funciona igual en escritorio (`python3 main.py`) y compilado a web con pygbag
(`pygbag main.py`), que requiere un punto de entrada asíncrono.
"""
import asyncio

from game.app import App


async def main():
    await App().run_async()


if __name__ == "__main__":
    asyncio.run(main())
