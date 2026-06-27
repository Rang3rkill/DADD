"""The whole game world.

This class owns the player, the farm tiles, the NPCs, the shop, the
dock/fishing area, the on-screen touch controls, and the HUD. The
farm and the dock share this one class and one coordinate space (no
camera, no scrolling) - `self.current_area` just decides which set of
things gets drawn and which interactions are valid. That's the simple
state-machine approach the README always pointed to as "the natural
next step once you add a second area" - a proper scene-manager class
becomes worth it once there's a third area, not before.

The pieces that *do* benefit from separation (crop growth, NPC
dialogue, gold/buy/sell rules, inventory counts) already live in their
own modules under game/entities and game/systems. World's job is to
wire them together, handle input, and draw.
"""

import random

import pygame

from game.config import (
    CHICKEN_PEN,
    CHICKEN_SPEED,
    COLOR_GOLD_TEXT,
    COLOR_GRASS,
    COLOR_PLAYER,
    COLOR_SOIL_DRY,
    COLOR_SOIL_TILLED,
    COLOR_TEXT_CREAM,
    COLOR_UI_PANEL,
    COLOR_UI_PANEL_BORDER,
    COLOR_WATER,
    COLOR_FISHING_SPOT,
    CROPS,
    DOCK_ENTRY_POS,
    DOCK_GATE_POS,
    DOCK_UNLOCK_COST,
    FARM_COLS,
    FARM_ENTRY_POS,
    FARM_GATE_POS,
    FARM_ORIGIN,
    FARM_ROWS,
    FISH,
    FISHING_SPOTS,
    INTERACTION_RADIUS,
    NEST_POS,
    NUM_CHICKENS,
    OBSTACLES,
    PLAYER_SIZE,
    PLAYER_SPEED,
    PLAYER_START,
    SELLABLES,
    SHOP_POS,
    TILE_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from game.entities.animal import Chicken
from game.entities.crop import Crop
from game.entities.nest import Nest
from game.entities.npc import NPC
from game.entities.obstacle import Obstacle
from game.npc_data import NPC_PROFILES
from game.systems.economy import Economy
from game.systems.inventory import Inventory

# Shop panel layout. Pulled out as constants (rather than magic
# numbers inline) since _build_shop_buttons and _draw_shop_panel both
# need to agree on them - if they drifted apart, buttons would render
# in the wrong place relative to the panel.
SHOP_TITLE_SPACE = 70
SHOP_ROW_WIDTH = 320
SHOP_ROW_HEIGHT = 32
SHOP_ROW_SPACING = 4
SHOP_CLOSE_BUTTON_SPACE = 60

# How long the player has to react once a fish bites.
FISHING_BITE_WINDOW_MS = 700


class Tile:
    def __init__(self, col, row, rect):
        self.col = col
        self.row = row
        self.rect = rect
        self.state = "untilled"  # "untilled" -> "tilled"
        self.crop = None


class Button:
    """A clickable rectangle with a label.

    Used both for the always-visible on-screen controls (so the game
    is playable on a phone with no keyboard) and for the shop menu.
    """

    def __init__(self, rect, label, on_click, font, bg=None, fg=None):
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.font = font
        self.bg = bg if bg is not None else COLOR_UI_PANEL
        self.fg = fg if fg is not None else COLOR_TEXT_CREAM

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, self.rect, width=2, border_radius=6)
        text = self.font.render(self.label, True, self.fg)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.on_click()
            return True
        return False


class World:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.font = pygame.font.SysFont("arial", 16)
        self.font_small = pygame.font.SysFont("arial", 13)
        self.font_title = pygame.font.SysFont("arial", 20, bold=True)

        self.player_pos = pygame.Vector2(PLAYER_START)
        self.player_rect = pygame.Rect(0, 0, *PLAYER_SIZE)
        self.player_rect.center = self.player_pos

        self.shop_pos = pygame.Vector2(SHOP_POS)
        self.dock_gate_pos = pygame.Vector2(DOCK_GATE_POS)
        self.farm_gate_pos = pygame.Vector2(FARM_GATE_POS)
        self.fishing_spots = [pygame.Vector2(p) for p in FISHING_SPOTS]

        self.inventory = Inventory()
        self.economy = Economy()
        self.npcs = self._build_npcs()
        self.obstacles = self._build_obstacles()
        self.animals = [Chicken(CHICKEN_PEN, CHICKEN_SPEED) for _ in range(NUM_CHICKENS)]
        self.nest = Nest(NEST_POS)

        self.selected_seed = "carrot"
        self.tiles = self._build_farm_grid()
        self.controls = self._build_controls()

        self.message_text = ""
        self.message_expires_at = 0

        self.shop_open = False
        self.shop_buttons = []

        # "farm" or "dock" - which area is currently active. See the
        # module docstring for why this is a flag rather than a full
        # scene-manager class.
        self.current_area = "farm"
        self.dock_unlocked = False

        # None when not fishing, otherwise a dict describing the
        # current attempt - see _start_fishing / _update_fishing.
        self.fishing = None

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------

    def _build_farm_grid(self):
        tiles = []
        ox, oy = FARM_ORIGIN
        for row in range(FARM_ROWS):
            tile_row = []
            for col in range(FARM_COLS):
                rect = pygame.Rect(
                    ox + col * TILE_SIZE, oy + row * TILE_SIZE,
                    TILE_SIZE - 2, TILE_SIZE - 2,
                )
                tile_row.append(Tile(col, row, rect))
            tiles.append(tile_row)
        return tiles

    def _build_npcs(self):
        npcs = []
        for profile in NPC_PROFILES.values():
            npcs.append(NPC(
                profile["name"],
                profile["pos"],
                profile["color"],
                profile["dialogue"],
                profile["gift_reactions"],
                self.font_small,
            ))
        return npcs

    def _build_obstacles(self):
        return [Obstacle(o["kind"], o["pos"], o.get("message")) for o in OBSTACLES]

    def _build_controls(self):
        controls = {}
        size = 44
        margin = 14
        base_x = margin
        base_y = WINDOW_HEIGHT - margin - size * 2

        # Directional pad - drawn for both desktop (cosmetic) and touch.
        # Movement reads these rects directly each frame; see
        # _update_movement, so they don't need on_click callbacks.
        noop = lambda: None
        controls["up"] = Button(pygame.Rect(base_x + size, base_y, size, size), "^", noop, self.font)
        controls["left"] = Button(pygame.Rect(base_x, base_y + size, size, size), "<", noop, self.font)
        controls["down"] = Button(pygame.Rect(base_x + size, base_y + size, size, size), "v", noop, self.font)
        controls["right"] = Button(pygame.Rect(base_x + size * 2, base_y + size, size, size), ">", noop, self.font)

        interact_rect = pygame.Rect(WINDOW_WIDTH - margin - 110, WINDOW_HEIGHT - margin - 100, 110, 44)
        gift_rect = pygame.Rect(WINDOW_WIDTH - margin - 110, WINDOW_HEIGHT - margin - 48, 110, 44)
        controls["interact"] = Button(interact_rect, "Interact (E)", self.handle_interact, self.font_small)
        controls["gift"] = Button(gift_rect, "Gift (G)", self.handle_gift, self.font_small)

        seed_y = 14
        controls["seed_carrot"] = Button(
            pygame.Rect(180, seed_y, 90, 28), "1: Carrot", lambda: self._select_seed("carrot"), self.font_small,
        )
        controls["seed_potato"] = Button(
            pygame.Rect(276, seed_y, 90, 28), "2: Potato", lambda: self._select_seed("potato"), self.font_small,
        )
        return controls

    # ---------------------------------------------------------------
    # Input
    # ---------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            self._handle_keydown(event.key)

    def _handle_click(self, pos):
        if self.shop_open:
            for button in self.shop_buttons:
                if button.handle_click(pos):
                    return
            return
        for name in ("interact", "gift", "seed_carrot", "seed_potato"):
            if self.controls[name].handle_click(pos):
                return

    def _handle_keydown(self, key):
        if key == pygame.K_ESCAPE and self.shop_open:
            self.close_shop()
            return
        if self.shop_open:
            return
        if key == pygame.K_e:
            self.handle_interact()
        elif key == pygame.K_g:
            self.handle_gift()
        elif key == pygame.K_1:
            self._select_seed("carrot")
        elif key == pygame.K_2:
            self._select_seed("potato")

    def _select_seed(self, crop_id):
        self.selected_seed = crop_id
        self.show_message(f"Selected {CROPS[crop_id]['name']} seeds.", 1200)

    # ---------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------

    def update(self, dt_ms):
        now = pygame.time.get_ticks()
        if not self.shop_open:
            self._update_movement(dt_ms)
        for row in self.tiles:
            for tile in row:
                if tile.crop:
                    tile.crop.update(now)
        for animal in self.animals:
            animal.update(dt_ms)
        self._update_fishing()

    def _update_movement(self, dt_ms):
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()

        def held(name):
            return mouse_pressed and self.controls[name].rect.collidepoint(mouse_pos)

        vx = 0
        vy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or held("left"):
            vx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d] or held("right"):
            vx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w] or held("up"):
            vy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s] or held("down"):
            vy += 1

        if vx == 0 and vy == 0:
            return

        move = pygame.Vector2(vx, vy).normalize() * PLAYER_SPEED * (dt_ms / 1000)

        # Resolved one axis at a time (rather than checking the
        # combined movement in one go) so the player slides along an
        # obstacle's edge instead of stopping dead the instant any
        # part of a diagonal move would collide.
        new_x = self.player_pos.x + move.x
        if self.current_area != "farm" or not self._collides_at(new_x, self.player_pos.y):
            self.player_pos.x = max(20, min(WINDOW_WIDTH - 20, new_x))

        new_y = self.player_pos.y + move.y
        if self.current_area != "farm" or not self._collides_at(self.player_pos.x, new_y):
            self.player_pos.y = max(20, min(WINDOW_HEIGHT - 20, new_y))

    def _collides_at(self, x, y):
        test_rect = pygame.Rect(0, 0, *PLAYER_SIZE)
        test_rect.center = (x, y)
        return any(test_rect.colliderect(obstacle.rect) for obstacle in self.obstacles)

    # ---------------------------------------------------------------
    # Interactions - shared helpers
    # ---------------------------------------------------------------

    def _nearby_npc(self):
        """Return the closest NPC within interaction range, or None."""
        closest = None
        closest_dist = INTERACTION_RADIUS
        for npc in self.npcs:
            dist = self.player_pos.distance_to(npc.pos)
            if dist < closest_dist:
                closest = npc
                closest_dist = dist
        return closest

    def _near_shop(self):
        return self.player_pos.distance_to(self.shop_pos) < INTERACTION_RADIUS

    def _near_dock_gate(self):
        return self.player_pos.distance_to(self.dock_gate_pos) < INTERACTION_RADIUS

    def _near_farm_gate(self):
        return self.player_pos.distance_to(self.farm_gate_pos) < INTERACTION_RADIUS

    def _tile_under_player(self):
        for row in self.tiles:
            for tile in row:
                if tile.rect.collidepoint(self.player_pos):
                    return tile
        return None

    def _nearby_fishing_spot(self):
        for spot in self.fishing_spots:
            if self.player_pos.distance_to(spot) < INTERACTION_RADIUS:
                return spot
        return None

    def _near_nest(self):
        return self.player_pos.distance_to(self.nest.pos) < INTERACTION_RADIUS

    def _nearby_obstacle_with_message(self):
        for obstacle in self.obstacles:
            if not obstacle.message:
                continue
            if self.player_pos.distance_to(obstacle.pos) < INTERACTION_RADIUS:
                return obstacle
        return None

    # ---------------------------------------------------------------
    # Interactions - farm area
    # ---------------------------------------------------------------

    def handle_interact(self):
        if self.shop_open:
            return

        if self.current_area == "dock":
            self._handle_dock_interact()
            return

        npc = self._nearby_npc()
        if npc:
            line = npc.talk()
            self.show_dialogue(npc.name, line)
            return

        if self._near_shop():
            self.open_shop()
            return

        if self._near_dock_gate():
            if self.dock_unlocked:
                self._enter_dock()
            else:
                self._try_unlock_dock()
            return

        if self._near_nest():
            self._collect_egg()
            return

        obstacle = self._nearby_obstacle_with_message()
        if obstacle:
            self.show_message(obstacle.message, 3500)
            return

        tile = self._tile_under_player()
        if tile is None:
            return

        if tile.state == "untilled":
            tile.state = "tilled"
            self.show_message("Tilled the soil.", 1200)
            return

        if tile.crop is None:
            seed_id = self.selected_seed
            if not self.inventory.has_seed(seed_id, 1):
                self.show_message(f"No {CROPS[seed_id]['name']} seeds. Buy some at the Market.", 1800)
                return
            self.inventory.remove_seed(seed_id, 1)
            tile.crop = Crop(seed_id, tile.rect.center, pygame.time.get_ticks())
            self.show_message(f"Planted {CROPS[seed_id]['name']}.", 1200)
            return

        if tile.crop.is_grown():
            name = tile.crop.data["name"]
            self.inventory.add_item(tile.crop.crop_id, 1)
            tile.crop = None
            self.show_message(f"Harvested {name}!", 1200)
            return

        self.show_message("Still growing...", 1000)

    def handle_gift(self):
        if self.shop_open:
            return
        if self.current_area != "farm":
            self.show_message("There's no one to gift here.", 1500)
            return

        npc = self._nearby_npc()
        if npc is None:
            self.show_message("There's no one nearby to give a gift to.", 1500)
            return

        gift_item_id = next((i for i in SELLABLES if self.inventory.has_item(i, 1)), None)
        if gift_item_id is None:
            self.show_message("You don't have anything to gift yet.", 1500)
            return

        self.inventory.remove_item(gift_item_id, 1)
        reaction = npc.receive_gift()
        self.show_dialogue(npc.name, reaction)

    def _try_unlock_dock(self):
        if self.economy.spend(DOCK_UNLOCK_COST):
            self.dock_unlocked = True
            self.show_message(f"Built a path to the Dock! (-{DOCK_UNLOCK_COST}g)", 1800)
        else:
            self.show_message(f"Need {DOCK_UNLOCK_COST}g to build a path to the Dock.", 1800)

    def _collect_egg(self):
        now = pygame.time.get_ticks()
        if not self.nest.is_ready(now):
            self.show_message("No egg ready yet.", 1200)
            return
        self.nest.collect(now)
        self.inventory.add_item("egg", 1)
        self.show_message("Collected an egg!", 1200)

    def _enter_dock(self):
        self.current_area = "dock"
        self.player_pos.update(DOCK_ENTRY_POS)
        self.fishing = None

    # ---------------------------------------------------------------
    # Interactions - dock area / fishing
    # ---------------------------------------------------------------

    def _handle_dock_interact(self):
        if self.fishing:
            self._resolve_fishing_attempt()
            return

        spot = self._nearby_fishing_spot()
        if spot:
            self._start_fishing(spot)
            return

        if self._near_farm_gate():
            self._enter_farm()
            return

        self.show_message("Nothing to do here.", 1000)

    def _enter_farm(self):
        self.current_area = "farm"
        self.player_pos.update(FARM_ENTRY_POS)

    def _start_fishing(self, spot):
        now = pygame.time.get_ticks()
        wait_ms = random.randint(1200, 3000)
        self.fishing = {
            "spot": spot,
            "phase": "waiting",
            "bite_at": now + wait_ms,
            "window_end": None,
        }
        self.show_message("Cast your line...", wait_ms + 1500)

    def _update_fishing(self):
        if not self.fishing:
            return
        now = pygame.time.get_ticks()
        if self.fishing["phase"] == "waiting" and now >= self.fishing["bite_at"]:
            self.fishing["phase"] = "biting"
            self.fishing["window_end"] = now + FISHING_BITE_WINDOW_MS
            self.show_message("Bite! Press Interact!", FISHING_BITE_WINDOW_MS + 100)
        elif self.fishing["phase"] == "biting" and now > self.fishing["window_end"]:
            self.show_message("It got away...", 1200)
            self.fishing = None

    def _resolve_fishing_attempt(self):
        if self.fishing["phase"] == "waiting":
            self.show_message("Too early - nothing happened.", 1200)
            self.fishing = None
            return

        fish_id = random.choice(list(FISH.keys()))
        self.inventory.add_item(fish_id, 1)
        self.show_message(f"Caught a {FISH[fish_id]['name']}!", 1500)
        self.fishing = None

    # ---------------------------------------------------------------
    # Shop
    # ---------------------------------------------------------------

    def open_shop(self):
        self.shop_open = True
        self._build_shop_buttons()

    def close_shop(self):
        self.shop_open = False
        self.shop_buttons = []

    def _shop_panel_rect(self):
        row_count = len(CROPS) + len(SELLABLES)
        height = SHOP_TITLE_SPACE + row_count * (SHOP_ROW_HEIGHT + SHOP_ROW_SPACING) + SHOP_CLOSE_BUTTON_SPACE
        rect = pygame.Rect(0, 0, 360, height)
        rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        return rect

    def _build_shop_buttons(self):
        self.shop_buttons = []
        panel = self._shop_panel_rect()
        x = panel.centerx - SHOP_ROW_WIDTH // 2
        y = panel.top + SHOP_TITLE_SPACE

        for crop_id, data in CROPS.items():
            label = f"Buy {data['name']} Seed - {data['seed_cost']}g"
            rect = pygame.Rect(x, y, SHOP_ROW_WIDTH, SHOP_ROW_HEIGHT)
            self.shop_buttons.append(Button(rect, label, lambda c=crop_id: self._buy_seed(c), self.font_small))
            y += SHOP_ROW_HEIGHT + SHOP_ROW_SPACING

        for item_id, data in SELLABLES.items():
            count = self.inventory.item_count(item_id)
            label = f"Sell All {data['name']}s (x{count}) - +{count * data['sell_price']}g"
            rect = pygame.Rect(x, y, SHOP_ROW_WIDTH, SHOP_ROW_HEIGHT)
            self.shop_buttons.append(Button(rect, label, lambda i=item_id: self._sell_all(i), self.font_small))
            y += SHOP_ROW_HEIGHT + SHOP_ROW_SPACING

        close_rect = pygame.Rect(panel.centerx - 60, y + 10, 120, 34)
        self.shop_buttons.append(Button(close_rect, "Close", self.close_shop, self.font_small))

    def _buy_seed(self, crop_id):
        if self.economy.buy_seed(self.inventory, crop_id):
            self.show_message(f"Bought 1 {CROPS[crop_id]['name']} seed.", 1200)
        else:
            self.show_message("Not enough gold.", 1200)
        self._build_shop_buttons()

    def _sell_all(self, item_id):
        count = self.inventory.item_count(item_id)
        name = SELLABLES[item_id]["name"]
        if count <= 0:
            self.show_message(f"No {name}s to sell.", 1200)
            return
        self.economy.sell_item(self.inventory, item_id, count)
        self.show_message(f"Sold {count} {name}.", 1200)
        self._build_shop_buttons()

    # ---------------------------------------------------------------
    # Messages / dialogue
    # ---------------------------------------------------------------

    def show_message(self, text, duration_ms):
        self.message_text = text
        self.message_expires_at = pygame.time.get_ticks() + duration_ms

    def show_dialogue(self, speaker, line):
        self.show_message(f"{speaker}: {line}", 3000)

    # ---------------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------------

    def draw(self):
        surface = self.screen

        if self.current_area == "dock":
            self._draw_dock_area(surface)
        else:
            self._draw_farm_area(surface)

        self._draw_player(surface)
        self._draw_top_bar(surface)
        self._draw_touch_controls(surface)
        self._draw_message(surface)

        if self.shop_open:
            self._draw_shop_panel(surface)

        pygame.display.flip()

    def _draw_farm_area(self, surface):
        surface.fill(COLOR_GRASS)

        self._draw_farm_tiles(surface)
        for row in self.tiles:
            for tile in row:
                if tile.crop:
                    tile.crop.draw(surface)

        for obstacle in self.obstacles:
            obstacle.draw(surface)

        self.nest.draw(surface, pygame.time.get_ticks())
        for animal in self.animals:
            animal.draw(surface)

        self._draw_shop_marker(surface)
        self._draw_dock_gate_marker(surface)
        for npc in self.npcs:
            npc.draw(surface)

    def _draw_dock_area(self, surface):
        surface.fill(COLOR_WATER)
        self._draw_farm_gate_marker(surface)
        self._draw_fishing_spots(surface)

    def _draw_farm_tiles(self, surface):
        for row in self.tiles:
            for tile in row:
                color = COLOR_SOIL_TILLED if tile.state == "tilled" else COLOR_SOIL_DRY
                pygame.draw.rect(surface, color, tile.rect, border_radius=4)

    def _draw_shop_marker(self, surface):
        rect = pygame.Rect(0, 0, 70, 70)
        rect.center = (int(self.shop_pos.x), int(self.shop_pos.y))
        pygame.draw.rect(surface, COLOR_UI_PANEL, rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, rect, width=2, border_radius=6)
        label = self.font_small.render("Market", True, COLOR_TEXT_CREAM)
        surface.blit(label, label.get_rect(center=rect.center))

    def _draw_dock_gate_marker(self, surface):
        rect = pygame.Rect(0, 0, 60, 90)
        rect.center = (int(self.dock_gate_pos.x), int(self.dock_gate_pos.y))
        pygame.draw.rect(surface, COLOR_UI_PANEL, rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, rect, width=2, border_radius=6)
        label_text = "To Dock" if self.dock_unlocked else f"Path ({DOCK_UNLOCK_COST}g)"
        label = self.font_small.render(label_text, True, COLOR_TEXT_CREAM)
        surface.blit(label, label.get_rect(center=rect.center))

    def _draw_farm_gate_marker(self, surface):
        rect = pygame.Rect(0, 0, 60, 90)
        rect.center = (int(self.farm_gate_pos.x), int(self.farm_gate_pos.y))
        pygame.draw.rect(surface, COLOR_UI_PANEL, rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, rect, width=2, border_radius=6)
        label = self.font_small.render("To Farm", True, COLOR_TEXT_CREAM)
        surface.blit(label, label.get_rect(center=rect.center))

    def _draw_fishing_spots(self, surface):
        for spot in self.fishing_spots:
            pygame.draw.circle(surface, COLOR_FISHING_SPOT, (int(spot.x), int(spot.y)), 16, width=3)
            is_biting = (
                self.fishing
                and self.fishing["spot"] == spot
                and self.fishing["phase"] == "biting"
            )
            if is_biting:
                label = self.font.render("!", True, COLOR_GOLD_TEXT)
                surface.blit(label, label.get_rect(center=(int(spot.x), int(spot.y) - 28)))

    def _draw_player(self, surface):
        self.player_rect.center = (int(self.player_pos.x), int(self.player_pos.y))
        pygame.draw.rect(surface, COLOR_PLAYER, self.player_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_UI_PANEL, self.player_rect, width=2, border_radius=4)

    def _draw_top_bar(self, surface):
        bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 50)
        pygame.draw.rect(surface, COLOR_UI_PANEL, bar_rect)

        self.controls["seed_carrot"].bg = (
            COLOR_UI_PANEL_BORDER if self.selected_seed == "carrot" else COLOR_UI_PANEL
        )
        self.controls["seed_potato"].bg = (
            COLOR_UI_PANEL_BORDER if self.selected_seed == "potato" else COLOR_UI_PANEL
        )
        self.controls["seed_carrot"].draw(surface)
        self.controls["seed_potato"].draw(surface)

        gold_text = self.font.render(f"Gold: {self.economy.gold}", True, COLOR_GOLD_TEXT)
        surface.blit(gold_text, (WINDOW_WIDTH - 250, 8))

        held = [
            f"{data['name']} x{self.inventory.item_count(item_id)}"
            for item_id, data in SELLABLES.items()
            if self.inventory.item_count(item_id) > 0
        ]
        inv_label = "   ".join(held) if held else "No items yet"
        inv_text = self.font_small.render(inv_label, True, COLOR_TEXT_CREAM)
        surface.blit(inv_text, (WINDOW_WIDTH - 250, 30))

        hint = self.font_small.render("WASD/Arrows: Move", True, COLOR_TEXT_CREAM)
        surface.blit(hint, (14, 16))

    def _draw_touch_controls(self, surface):
        for name in ("up", "down", "left", "right", "interact", "gift"):
            self.controls[name].draw(surface)

    def _draw_message(self, surface):
        now = pygame.time.get_ticks()
        if not self.message_text or now > self.message_expires_at:
            return
        box = pygame.Rect(0, 0, 600, 50)
        box.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 190)
        pygame.draw.rect(surface, COLOR_UI_PANEL, box, border_radius=8)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, box, width=2, border_radius=8)
        text = self.font.render(self.message_text, True, COLOR_TEXT_CREAM)
        surface.blit(text, text.get_rect(center=box.center))

    def _draw_shop_panel(self, surface):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        panel = self._shop_panel_rect()
        pygame.draw.rect(surface, COLOR_UI_PANEL, panel, border_radius=10)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, panel, width=2, border_radius=10)

        title = self.font_title.render("Market", True, COLOR_TEXT_CREAM)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 26)))

        for button in self.shop_buttons:
            button.draw(surface)
