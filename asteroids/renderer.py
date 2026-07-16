"""Presentation layer for the Asteroids game session."""

from pathlib import Path

import pygame

from .constants import (
    BACKGROUND_IMAGE,
    CYAN,
    HUD_PANEL,
    MUTED,
    ORANGE,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    VIOLET,
    WHITE,
)


class GameRenderer:
    """Render the playfield, HUD, and session overlays."""

    def __init__(self, screen):
        self.screen = screen
        self.background = self._load_background()
        self.font_small = pygame.font.SysFont("consolas", 18)
        self.font_medium = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_large = pygame.font.SysFont("consolas", 66, bold=True)

    def _load_background(self):
        background_path = Path(__file__).resolve().parent / BACKGROUND_IMAGE
        try:
            image = pygame.image.load(background_path).convert()
            if image.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
                image = pygame.transform.smoothscale(
                    image, (SCREEN_WIDTH, SCREEN_HEIGHT)
                )
            return image
        except (FileNotFoundError, pygame.error):
            fallback = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fallback.fill((2, 5, 14))
            return fallback

    def draw(
        self,
        drawable,
        player,
        score,
        lives,
        game_over,
    ):
        self.screen.blit(self.background, (0, 0))
        for sprite in drawable:
            sprite.draw(self.screen)
        self._draw_hud(player, score, lives)

        if game_over:
            self._draw_game_over(score)
        elif not player.active:
            self._draw_center_message("RESPAWNING...")

        pygame.display.flip()

    def _draw_hud(self, player, score, lives):
        panel = pygame.Surface((SCREEN_WIDTH, 82), pygame.SRCALPHA)
        panel.fill(HUD_PANEL)
        self.screen.blit(panel, (0, 0))

        self._blit_text(f"SCORE {score:06d}", (24, 15), self.font_medium, WHITE)
        self._blit_text(
            f"WEAPON  {player.weapon_name.upper()}",
            (24, 49),
            self.font_small,
            CYAN,
        )

        self._blit_text("LIVES", (SCREEN_WIDTH / 2 - 65, 18), self.font_small, MUTED)
        for index in range(lives):
            center = pygame.Vector2(SCREEN_WIDTH / 2 + 8 + index * 28, 30)
            points = [
                center + pygame.Vector2(0, -9),
                center + pygame.Vector2(-7, 8),
                center + pygame.Vector2(7, 8),
            ]
            pygame.draw.polygon(self.screen, WHITE, points, width=2)

        bomb_text = (
            "BOMB READY"
            if player.bomb_cooldown_timer <= 0
            else f"BOMB {player.bomb_cooldown_timer:0.1f}s"
        )
        self._blit_text(bomb_text, (SCREEN_WIDTH - 180, 15), self.font_small, VIOLET)

        effects = []
        if player.shield_timer > 0:
            effects.append(f"SHIELD {player.shield_timer:0.1f}s")
        if player.speed_timer > 0:
            effects.append(f"SPEED {player.speed_timer:0.1f}s")
        if effects:
            self._blit_text(
                "  ".join(effects),
                (SCREEN_WIDTH - 300, 49),
                self.font_small,
                CYAN if player.shield_timer > 0 else ORANGE,
            )

        controls = "W/S THRUST  A/D TURN  SPACE FIRE  |  1/2/3 WEAPONS  B BOMB"
        text_surface = self.font_small.render(controls, True, MUTED)
        self.screen.blit(
            text_surface,
            (SCREEN_WIDTH - text_surface.get_width() - 18, SCREEN_HEIGHT - 30),
        )

    def _draw_game_over(self, score_value):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 8, 190))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("GAME OVER", True, RED)
        score = self.font_medium.render(f"FINAL SCORE  {score_value:06d}", True, WHITE)
        prompt = self.font_small.render(
            "Press R to restart  |  Esc to quit", True, MUTED
        )
        center_x = SCREEN_WIDTH / 2
        self.screen.blit(title, (center_x - title.get_width() / 2, 250))
        self.screen.blit(score, (center_x - score.get_width() / 2, 345))
        self.screen.blit(prompt, (center_x - prompt.get_width() / 2, 395))

    def _draw_center_message(self, message):
        surface = self.font_medium.render(message, True, WHITE)
        backing = pygame.Surface(
            (surface.get_width() + 36, surface.get_height() + 22), pygame.SRCALPHA
        )
        backing.fill((0, 0, 8, 150))
        position = (
            SCREEN_WIDTH / 2 - backing.get_width() / 2,
            SCREEN_HEIGHT / 2 - backing.get_height() / 2,
        )
        self.screen.blit(backing, position)
        self.screen.blit(surface, (position[0] + 18, position[1] + 11))

    def _blit_text(
        self,
        text,
        position,
        font,
        color,
    ):
        self.screen.blit(font.render(text, True, color), position)
