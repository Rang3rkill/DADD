"""Entry point.

Structured for pygbag - the tool that packages this to run in a
browser. Its one real requirement is that the main loop is async and
yields once per frame via `await asyncio.sleep(0)`. That's the only
pygbag-specific thing in this file; everything else is normal Pygame.
This same structure also runs fine as a plain desktop app via
`python main.py`.
"""

import asyncio

import pygame

from game.config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from game.world import World


async def main():
    pygame.init()
    pygame.display.set_caption("Farm Prototype")
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    world = World()

    running = True
    while running:
        dt_ms = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                world.handle_event(event)

        world.update(dt_ms)
        world.draw()

        await asyncio.sleep(0)  # required by pygbag - hands control back each frame

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
