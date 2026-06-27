"""The whole game world.

This single class owns the player, the farm tiles, the NPC, the shop,
the on-screen touch controls, and the HUD. That's a lot in one file -
but the world is a single non-scrolling screen, so there's no scene
transition or camera logic that would justify splitting into multiple
Phaser/Unity-style "scenes" yet. The pieces that *do* benefit from
separation (crop growth, the NPC's dialogue, gold/buy/sell rules,
inventory counts) already live in their own modules under
game/entities and game/systems. World's job is just to wire them
together, handle input, and draw.

If you add a second area (e.g. a fishing dock) later, that's the
natural point to introduce a proper scene/state system instead of
growing this file further.
"""

import pygame

from game.config import (
    COLOR_GOLD_TEXT,
    COLOR_GRASS,
    COLOR_PLAYER,
    COLOR_SOIL_DRY,
    COLOR_SOIL_TILLED,
    COLOR_TEXT_CREAM,
    COLOR_UI_PANEL,
    COLOR_UI_PANEL_BORDER,
    CROPS,
    FARM_COLS,
    FARM_ORIGIN,
    FARM_ROWS,
    INTERACTION_RADIUS,
    NPC_POS,
    PLAYER_SIZE,
    PLAYER_SPEED,
    PLAYER_START,
    SHOP_POS,
    TILE_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from game.entities.crop import Crop
from game.entities.npc import NPC
from game.systems.economy import Economy
from game.systems.inventory import Inventory


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

        self.inventory = Inventory()
        self.economy = Economy()
        self.npc = NPC("Maple", NPC_POS, self.font_small)

        self.selected_seed = "carrot"
        self.tiles = self._build_farm_grid()
        self.controls = self._build_controls()

        self.message_text = ""
        self.message_expires_at = 0

        self.shop_open = False
        self.shop_buttons = []

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
        self.player_pos += move
        self.player_pos.x = max(20, min(WINDOW_WIDTH - 20, self.player_pos.x))
        self.player_pos.y = max(20, min(WINDOW_HEIGHT - 20, self.player_pos.y))

    # ---------------------------------------------------------------
    # Interactions
    # ---------------------------------------------------------------

    def _near_npc(self):
        return self.player_pos.distance_to(self.npc.pos) < INTERACTION_RADIUS

    def _near_shop(self):
        return self.player_pos.distance_to(self.shop_pos) < INTERACTION_RADIUS

    def _tile_under_player(self):
        for row in self.tiles:
            for tile in row:
                if tile.rect.collidepoint(self.player_pos):
                    return tile
        return None

    def handle_interact(self):
        if self.shop_open:
            return
        if self._near_npc():
            line = self.npc.talk()
            self.show_dialogue(self.npc.name, line)
            return
        if self._near_shop():
            self.open_shop()
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
            self.inventory.add_crop(tile.crop.crop_id, 1)
            tile.crop = None
            self.show_message(f"Harvested {name}!", 1200)
            return

        self.show_message("Still growing...", 1000)

    def handle_gift(self):
        if self.shop_open:
            return
        if not self._near_npc():
            self.show_message(f"Get closer to {self.npc.name} to give a gift.", 1500)
            return

        gift_crop_id = next((c for c in CROPS if self.inventory.has_crop(c, 1)), None)
        if gift_crop_id is None:
            self.show_message("You don't have any crops to gift yet.", 1500)
            return

        self.inventory.remove_crop(gift_crop_id, 1)
        reaction = self.npc.receive_gift()
        self.show_dialogue(self.npc.name, reaction)

    # ---------------------------------------------------------------
    # Shop
    # ---------------------------------------------------------------

    def open_shop(self):
        self.shop_open = True
        self._build_shop_buttons()

    def close_shop(self):
        self.shop_open = False
        self.shop_buttons = []

    def _build_shop_buttons(self):
        self.shop_buttons = []
        panel_x = WINDOW_WIDTH // 2 - 160
        y = WINDOW_HEIGHT // 2 - 130
        row_h = 42

        for crop_id, data in CROPS.items():
            label = f"Buy {data['name']} Seed - {data['seed_cost']}g"
            rect = pygame.Rect(panel_x, y, 320, 34)
            self.shop_buttons.append(Button(rect, label, lambda c=crop_id: self._buy_seed(c), self.font_small))
            y += row_h

        for crop_id, data in CROPS.items():
            count = self.inventory.crop_count(crop_id)
            label = f"Sell All {data['name']}s (x{count}) - +{count * data['sell_price']}g"
            rect = pygame.Rect(panel_x, y, 320, 34)
            self.shop_buttons.append(Button(rect, label, lambda c=crop_id: self._sell_all(c), self.font_small))
            y += row_h

        close_rect = pygame.Rect(panel_x + 100, y + 12, 120, 34)
        self.shop_buttons.append(Button(close_rect, "Close", self.close_shop, self.font_small))

    def _buy_seed(self, crop_id):
        if self.economy.buy_seed(self.inventory, crop_id):
            self.show_message(f"Bought 1 {CROPS[crop_id]['name']} seed.", 1200)
        else:
            self.show_message("Not enough gold.", 1200)
        self._build_shop_buttons()

    def _sell_all(self, crop_id):
        count = self.inventory.crop_count(crop_id)
        if count <= 0:
            self.show_message(f"No {CROPS[crop_id]['name']} to sell.", 1200)
            return
        self.economy.sell_crop(self.inventory, crop_id, count)
        self.show_message(f"Sold {count} {CROPS[crop_id]['name']}.", 1200)
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
        surface.fill(COLOR_GRASS)

        self._draw_farm_tiles(surface)
        for row in self.tiles:
            for tile in row:
                if tile.crop:
                    tile.crop.draw(surface)

        self._draw_shop_marker(surface)
        self.npc.draw(surface)
        self._draw_player(surface)

        self._draw_top_bar(surface)
        self._draw_touch_controls(surface)
        self._draw_message(surface)

        if self.shop_open:
            self._draw_shop_panel(surface)

        pygame.display.flip()

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

        carrots = self.inventory.crop_count("carrot")
        potatoes = self.inventory.crop_count("potato")
        inv_text = self.font_small.render(f"Carrots: {carrots}   Potatoes: {potatoes}", True, COLOR_TEXT_CREAM)
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

        panel = pygame.Rect(0, 0, 360, 320)
        panel.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        pygame.draw.rect(surface, COLOR_UI_PANEL, panel, border_radius=10)
        pygame.draw.rect(surface, COLOR_UI_PANEL_BORDER, panel, width=2, border_radius=10)

        title = self.font_title.render("Market", True, COLOR_TEXT_CREAM)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 26)))

        for button in self.shop_buttons:
            button.draw(surface)
