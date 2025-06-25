import pygame
import random
import sys
import math
import json
from enum import Enum

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen setup
SCREEN_INFO = pygame.display.Info()
WIDTH, HEIGHT = SCREEN_INFO.current_w, SCREEN_INFO.current_h
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("🚀 Advanced Rocket Shooter")

# Fonts
FONT_SM = pygame.font.SysFont("monospace", int(HEIGHT / 40))
FONT_MD = pygame.font.SysFont("monospace", int(HEIGHT / 30))
FONT_LG = pygame.font.SysFont("monospace", int(HEIGHT / 20))
FONT_XL = pygame.font.SysFont("monospace", int(HEIGHT / 10))

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)


# Game states
class GameState(Enum):
    START_MENU = 0
    SETTINGS = 1
    PLAYING = 2
    GAME_OVER = 3
    SHOP = 4
    PAUSED = 5
    TUTORIAL = 6
    LEVEL_COMPLETE = 7
    STORY = 8
    ACHIEVEMENTS = 9
    CHALLENGES = 10
    LEVEL_SELECT = 11


# Player class
class Player:
    def __init__(self, x_position=None):
        self.width = 40
        self.height = 50
        start_x = WIDTH // 2 - self.width // 2 if x_position is None else x_position
        self.rect = pygame.Rect(start_x, HEIGHT - self.height - 20, self.width, self.height)
        self.speed = 6
        self.health = 100
        self.max_health = 100
        self.coins = 50
        self.weapon_type = "laser"  # laser, missile, plasma
        self.weapon_power = 1
        self.weapons_unlocked = ["laser"]
        self.rapid_fire = False
        self.shield = False
        self.shield_timer = 0
        self.score = 0
        self.lives = 3
        self.rocket_type = "basic"  # basic, advanced, ultimate
        self.kills = 0
        self.shoot_cooldown = 0
        self.rapid_fire_timer = 0

    def move(self, dx):
        self.rect.x += dx
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def take_damage(self, amount):
        if self.shield:
            return False
        self.health -= amount
        return True

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def add_coins(self, amount):
        self.coins += amount

    def unlock_weapon(self, weapon):
        if weapon not in self.weapons_unlocked:
            self.weapons_unlocked.append(weapon)
            return True
        return False

    def upgrade_weapon(self):
        if self.coins >= 50 * self.weapon_power:
            self.coins -= 50 * self.weapon_power
            self.weapon_power = min(5, self.weapon_power + 1)
            return True
        return False

    def upgrade_rocket(self, rocket_type):
        costs = {"advanced": 200, "ultimate": 500}
        if rocket_type in costs and self.coins >= costs[rocket_type]:
            self.coins -= costs[rocket_type]
            self.rocket_type = rocket_type
            if rocket_type == "advanced":
                self.max_health = 150
                self.health = min(150, self.health)
            elif rocket_type == "ultimate":
                self.max_health = 200
                self.health = min(200, self.health)
            return True
        return False

    def activate_shield(self, duration=300):
        self.shield = True
        self.shield_timer = duration

    def update(self):
        if self.shield:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield = False

        if self.rapid_fire:
            self.rapid_fire_timer -= 1
            if self.rapid_fire_timer <= 0:
                self.rapid_fire = False

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def switch_weapon(self, weapon):
        if weapon in self.weapons_unlocked:
            self.weapon_type = weapon
            return True
        return False

    def draw(self, surface):
        # Draw rocket based on type
        if self.rocket_type == "basic":
            color = (0, 255, 255)
            engine_color = (0, 180, 180)
        elif self.rocket_type == "advanced":
            color = (255, 165, 0)
            engine_color = (200, 100, 0)
        else:  # ultimate
            color = (255, 50, 255)
            engine_color = (180, 0, 180)

        # Draw rocket body
        pygame.draw.polygon(surface, color, [
            (self.rect.centerx, self.rect.top),
            (self.rect.left, self.rect.bottom),
            (self.rect.right, self.rect.bottom)
        ])
        pygame.draw.rect(surface, engine_color, (self.rect.left + 15, self.rect.top + 20, 10, 20))

        # Draw engines (flame effect)
        flame_length = random.randint(5, 10)
        flame_color = (255, random.randint(100, 200), 0)  # RGB: red-orange
        pygame.draw.polygon(surface, flame_color, [
            (self.rect.left + 5, self.rect.bottom),
            (self.rect.left + 15, self.rect.bottom + flame_length),
            (self.rect.right - 15, self.rect.bottom + flame_length),
            (self.rect.right - 5, self.rect.bottom)
        ])
        # Draw shield if active
        if self.shield:
            shield_color = (0, 100, 255)
            pygame.draw.circle(surface, shield_color, self.rect.center, self.rect.width, 2)

    def draw_health_bar(self, surface, y_offset=10):
        bar_width = 200
        bar_height = 20
        fill = (self.health / self.max_health) * bar_width
        outline_rect = pygame.Rect(10, y_offset, bar_width, bar_height)
        fill_rect = pygame.Rect(10, y_offset, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)
        health_text = FONT_SM.render(f"Health: {self.health}/{self.max_health}", True, WHITE)
        surface.blit(health_text, (15, y_offset + 2))


# Enemy types
class EnemyType(Enum):
    ASTEROID = 0
    SCOUT = 1
    FIGHTER = 2
    BOMBER = 3
    ELITE = 4


class Enemy:
    def __init__(self, x, y, enemy_type, level):
        self.type = enemy_type
        self.level = level

        if enemy_type == EnemyType.ASTEROID:
            self.width = 30 + random.randint(-5, 10)
            self.height = self.width
            self.speed = random.uniform(1.0 + level * 0.2, 2.0 + level * 0.4)
            self.health = 1
            self.color = (100, 255, 100)
            self.value = 1
            self.shoot_cooldown = 0
            self.drop_chance = 0.3

        elif enemy_type == EnemyType.SCOUT:
            self.width = 40
            self.height = 30
            self.speed = random.uniform(2.0 + level * 0.3, 3.0 + level * 0.5)
            self.health = 2 + level // 2
            self.color = (random.randint(150, 255), random.randint(50, 150), random.randint(50, 150))
            self.value = 2
            self.shoot_cooldown = random.randint(80, 120)
            self.drop_chance = 0.4

        elif enemy_type == EnemyType.FIGHTER:
            self.width = 50
            self.height = 40
            self.speed = random.uniform(1.5 + level * 0.2, 2.5 + level * 0.4)
            self.health = 3 + level
            self.color = (200, 50, 50)
            self.value = 5
            self.shoot_cooldown = random.randint(60, 90)
            self.drop_chance = 0.5

        elif enemy_type == EnemyType.BOMBER:
            self.width = 60
            self.height = 40
            self.speed = random.uniform(1.0 + level * 0.2, 1.8 + level * 0.3)
            self.health = 5 + level * 2
            self.color = (100, 100, 200)
            self.value = 10
            self.shoot_cooldown = random.randint(90, 150)
            self.drop_chance = 0.6

        elif enemy_type == EnemyType.ELITE:
            self.width = 70
            self.height = 50
            self.speed = random.uniform(2.5 + level * 0.3, 3.5 + level * 0.5)
            self.health = 8 + level * 3
            self.color = (200, 200, 50)
            self.value = 20
            self.shoot_cooldown = random.randint(50, 80)
            self.drop_chance = 0.7

        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.original_pos = (x, y)
        self.angle = 0
        self.oscillation = random.uniform(0.02, 0.05)

    def move(self):
        if self.type == EnemyType.ASTEROID:
            self.rect.y += self.speed
        else:
            # More advanced movement patterns for ships
            self.rect.y += self.speed * 0.7
            self.angle += self.oscillation
            self.rect.x = self.original_pos[0] + math.sin(self.angle) * 100

    def update_cooldown(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def can_shoot(self):
        return self.shoot_cooldown <= 0 and self.type != EnemyType.ASTEROID

    def reset_cooldown(self):
        if self.type == EnemyType.SCOUT:
            self.shoot_cooldown = random.randint(80, 120)
        elif self.type == EnemyType.FIGHTER:
            self.shoot_cooldown = random.randint(60, 90)
        elif self.type == EnemyType.BOMBER:
            self.shoot_cooldown = random.randint(90, 150)
        elif self.type == EnemyType.ELITE:
            self.shoot_cooldown = random.randint(50, 80)

    def draw(self, surface):
        if self.type == EnemyType.ASTEROID:
            pygame.draw.circle(surface, self.color, self.rect.center, self.rect.width // 2)
            pygame.draw.circle(surface, (40, 140, 40), self.rect.center, self.rect.width // 4)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
            # Draw cockpit
            pygame.draw.circle(surface, (50, 50, 50),
                               (self.rect.centerx, self.rect.centery),
                               self.rect.width // 4)


# Boss class
class Boss:
    def __init__(self, level):
        self.width = 200 + level * 10
        self.height = 80 + level * 5
        self.rect = pygame.Rect(WIDTH // 2 - self.width // 2, 50, self.width, self.height)
        self.speed = 1 + level * 0.2
        self.health = 50 * level
        self.max_health = 50 * level
        self.direction = 1  # 1 for right, -1 for left
        self.shoot_cooldown = 40 - min(5, level)  # More time between shots
        self.attack_pattern = 0
        self.attack_timer = 0
        self.color = (200, 0, 0)
        self.shield_active = False
        self.shield_timer = 0
        self.level = level
        self.value = 100 * level
        self.shield_cooldown = 120  # Cooldown before shield can be activated again

    def move(self):
        self.rect.x += self.speed * self.direction
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.direction *= -1
            self.rect.y += 20  # Move down when hitting a wall

    def update_cooldown(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def reset_cooldown(self):
        self.shoot_cooldown = 40 - min(5, self.level)  # Faster shooting at higher levels

    def activate_shield(self):
        if self.shield_cooldown <= 0:
            self.shield_active = True
            self.shield_timer = 120  # 2 seconds for shield
            self.shield_cooldown = 180  # 3 seconds cooldown

    def update_shield(self):
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

    def take_damage(self, amount):
        if self.shield_active:
            return False
        self.health = max(0, self.health - amount)
        return True

    def draw(self, surface):
        # Draw boss body
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)

        # Draw shield if active
        if self.shield_active:
            shield_color = (0, 100, 255)
            pygame.draw.rect(surface, shield_color, self.rect.inflate(20, 20), 3, border_radius=15)

        # Draw health bar
        health_width = 300
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, (100, 100, 100),
                         (self.rect.centerx - health_width // 2, self.rect.top - 30, health_width, 15))
        pygame.draw.rect(surface, (0, 255, 0),
                         (self.rect.centerx - health_width // 2, self.rect.top - 30, health_width * health_ratio, 15))

        # Draw details
        pygame.draw.circle(surface, (50, 50, 50), (self.rect.centerx, self.rect.centery), 20)
        pygame.draw.circle(surface, (150, 150, 255), (self.rect.centerx, self.rect.centery), 10)

        # Draw level indicator
        level_text = FONT_MD.render(f"BOSS LEVEL {self.level}", True, RED)
        surface.blit(level_text, (self.rect.centerx - level_text.get_width() // 2, self.rect.top - 50))


# Weapon types
class WeaponType(Enum):
    LASER = 0
    MISSILE = 1
    PLASMA = 2


class Projectile:
    def __init__(self, x, y, weapon_type, power):
        self.type = weapon_type
        self.power = power

        if weapon_type == WeaponType.LASER:
            self.width = 4
            self.height = 15
            self.speed = 15
            self.color = (255, 60, 60)
            self.damage = 10 * power

        elif weapon_type == WeaponType.MISSILE:
            self.width = 8
            self.height = 20
            self.speed = 10
            self.color = (255, 165, 0)
            self.damage = 25 * power
            self.homing = True

        elif weapon_type == WeaponType.PLASMA:
            self.width = 15
            self.height = 15
            self.speed = 8
            self.color = (0, 255, 255)
            self.damage = 40 * power
            self.explosive = True

        self.rect = pygame.Rect(x - self.width // 2, y - self.height, self.width, self.height)

    def move(self):
        self.rect.y -= self.speed

    def draw(self, surface):
        if self.type == WeaponType.LASER:
            pygame.draw.line(surface, self.color,
                             (self.rect.centerx, self.rect.bottom),
                             (self.rect.centerx, self.rect.top), 4)
        elif self.type == WeaponType.MISSILE:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.polygon(surface, (255, 200, 0), [
                (self.rect.left, self.rect.bottom),
                (self.rect.right, self.rect.bottom),
                (self.rect.centerx, self.rect.bottom + 10)
            ])
        elif self.type == WeaponType.PLASMA:
            pygame.draw.circle(surface, self.color, self.rect.center, self.rect.width // 2)


# Power-up types
class PowerUpType(Enum):
    COIN = 0
    HEALTH = 1
    RAPID_FIRE = 2
    SHIELD = 3
    BOMB = 4
    GUN = 5


class PowerUp:
    def __init__(self, x, y, type):
        self.type = type
        self.rect = pygame.Rect(x, y, 30, 30)
        self.speed = 2
        self.colors = {
            PowerUpType.COIN: (255, 215, 0),
            PowerUpType.HEALTH: (255, 50, 50),
            PowerUpType.RAPID_FIRE: (50, 255, 50),
            PowerUpType.SHIELD: (50, 50, 255),
            PowerUpType.BOMB: (255, 0, 0),
            PowerUpType.GUN: (180, 0, 180)
        }
        self.symbols = {
            PowerUpType.COIN: "$",
            PowerUpType.HEALTH: "+",
            PowerUpType.RAPID_FIRE: "⚡",
            PowerUpType.SHIELD: "🛡️",
            PowerUpType.BOMB: "💣",
            PowerUpType.GUN: "🔫"
        }

    def move(self):
        self.rect.y += self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, self.colors[self.type], self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        symbol = FONT_MD.render(self.symbols[self.type], True, WHITE)
        surface.blit(symbol, (self.rect.centerx - symbol.get_width() // 2,
                              self.rect.centery - symbol.get_height() // 2))


# Game class
class Game:
    def __init__(self):
        self.state = GameState.START_MENU
        self.player = Player()
        self.player2 = None
        self.level = 1
        self.max_level = 100
        self.unlocked_levels = 1
        self.high_score = 0
        self.load_high_score()
        self.clock = pygame.time.Clock()
        self.stars = self.create_stars(200)
        self.projectiles = []
        self.enemies = []
        self.enemy_projectiles = []
        self.power_ups = []
        self.boss = None
        self.boss_active = False
        self.camera_shake = 0
        self.camera_offset = (0, 0)
        self.rapid_fire_active = False
        self.rapid_fire_timer = 0
        self.score = 0
        self.achievements = self.load_achievements()
        self.challenges = self.load_challenges()
        self.settings = {
            "sound": True,
            "music": True,
            "controls": {
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "fire": pygame.K_SPACE,
                "pause": pygame.K_p
            },
            "difficulty": "normal",
            "two_players": False
        }
        self.tutorial_step = 0
        self.story_index = 0
        self.endless_mode = False
        self.enemies_defeated = 0
        self.enemies_to_defeat = 10
        self.explosions = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 60  # frames between enemy spawns
        self.level_stats = {
            "coins_collected": 0,
            "enemies_killed": 0,
            "damage_taken": 0,
            "time_taken": 0
        }
        self.level_start_time = pygame.time.get_ticks()
        self.level_complete_time = 0

        # Story text
        self.story = [
            "Year 2150: Earth's resources are depleted.",
            "You are Captain Nova, pilot of the last hope ship.",
            "Your mission: Find a new habitable planet.",
            "But hostile alien forces stand in your way...",
            "Defeat them and save humanity!"
        ]

        # Tutorial text
        self.tutorial_text = [
            "Welcome to Space Shooter!",
            "Move with LEFT and RIGHT arrow keys",
            "Press SPACE to shoot lasers",
            "Press 1-3 to switch weapons",
            "Collect coins to buy upgrades in the shop",
            "Destroy enemies to earn points",
            "Avoid enemy fire and asteroids",
            "Defeat the boss at the end of each level",
            "Good luck, Captain!"
        ]

        # Create some initial achievements
        if not self.achievements:
            self.achievements = [
                {"name": "First Blood", "description": "Destroy your first enemy", "unlocked": False},
                {"name": "Coin Collector", "description": "Collect 100 coins", "unlocked": False},
                {"name": "Boss Slayer", "description": "Defeat your first boss", "unlocked": False},
                {"name": "Weapon Master", "description": "Unlock all weapons", "unlocked": False},
                {"name": "Ultimate Pilot", "description": "Complete all levels", "unlocked": False}
            ]

        # Create some initial challenges
        if not self.challenges:
            self.challenges = [
                {"name": "No Damage", "description": "Complete a level without taking damage", "reward": 100,
                 "completed": False},
                {"name": "Boss Rush", "description": "Defeat a boss in under 30 seconds", "reward": 200,
                 "completed": False},
                {"name": "Coin Hoarder", "description": "Collect 50 coins in one level", "reward": 150,
                 "completed": False},
                {"name": "Perfect Accuracy", "description": "Destroy 20 enemies without missing", "reward": 100,
                 "completed": False}
            ]

    def create_stars(self, count):
        stars = []
        for _ in range(count):
            stars.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "r": random.randint(1, 3),
                "speed": random.uniform(0.5, 2)
            })
        return stars

    def draw_stars(self, surface):
        for star in self.stars:
            pygame.draw.circle(surface, WHITE, (star["x"], star["y"]), star["r"])
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

    def draw_ui(self, surface):
        # Draw score
        score_text = FONT_MD.render(f"Score: {self.player.score}", True, WHITE)
        surface.blit(score_text, (WIDTH - score_text.get_width() - 10, 10))

        # Draw level
        level_text = FONT_MD.render(f"Level: {self.level}", True, WHITE)
        surface.blit(level_text, (WIDTH - level_text.get_width() - 10, 50))

        # Draw coins
        coins_text = FONT_MD.render(f"Coins: {self.player.coins}", True, YELLOW)
        surface.blit(coins_text, (10, 40))

        # Draw health bar
        self.player.draw_health_bar(surface)

        # Draw player 2 health if two players
        if self.player2:
            self.player2.draw_health_bar(surface, 70)

        # Draw weapon info
        weapon_text = FONT_SM.render(f"Weapon: {self.player.weapon_type.title()} (Lvl {self.player.weapon_power})",
                                     True, CYAN)
        surface.blit(weapon_text, (WIDTH - weapon_text.get_width() - 10, 90))

        # Draw weapon controls
        weapons_text = FONT_SM.render("Weapons: 1-Laser 2-Missile 3-Plasma", True, CYAN)
        surface.blit(weapons_text, (10, HEIGHT - 30))

        # Draw active power-ups
        y_offset = 130
        if self.player.shield:
            shield_text = FONT_SM.render("SHIELD ACTIVE", True, BLUE)
            surface.blit(shield_text, (WIDTH - shield_text.get_width() - 10, y_offset))
            y_offset += 30

        if self.player.rapid_fire:
            rapid_text = FONT_SM.render("RAPID FIRE ACTIVE", True, GREEN)
            surface.blit(rapid_text, (WIDTH - rapid_text.get_width() - 10, y_offset))
            y_offset += 30

    def draw_game_over(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        title = FONT_XL.render("GAME OVER", True, RED)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        score_text = FONT_LG.render(f"Final Score: {self.player.score}", True, WHITE)
        surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 3 + 50))

        restart_text = FONT_MD.render("Press R to Restart or ESC for Menu", True, GREEN)
        surface.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2))

        # Update high score if needed
        if self.player.score > self.high_score:
            self.high_score = self.player.score
            self.save_high_score()
            new_high = FONT_LG.render("NEW HIGH SCORE!", True, YELLOW)
            surface.blit(new_high, (WIDTH // 2 - new_high.get_width() // 2, HEIGHT // 2 + 80))

    def draw_start_menu(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("🚀 SPACE SHOOTER", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 6))

        # Menu options
        options = [
            ("Start Game", GameState.PLAYING),
            ("Level Select", GameState.LEVEL_SELECT),
            ("Tutorial", GameState.TUTORIAL),
            ("Settings", GameState.SETTINGS),
            ("Achievements", GameState.ACHIEVEMENTS),
            ("Challenges", GameState.CHALLENGES),
            ("Quit", None)
        ]

        mouse_pos = pygame.mouse.get_pos()

        for i, (text, state) in enumerate(options):
            y_pos = HEIGHT // 3 + i * 60
            text_surf = FONT_LG.render(text, True, WHITE)
            rect = pygame.Rect(WIDTH // 2 - 150, y_pos, 300, 50)

            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (50, 50, 100), rect, border_radius=10)
                if pygame.mouse.get_pressed()[0]:
                    if state is None:
                        pygame.quit()
                        sys.exit()
                    self.state = state
                    if state == GameState.PLAYING:
                        self.reset_game()
            else:
                pygame.draw.rect(surface, (30, 30, 60), rect, border_radius=10)

            pygame.draw.rect(surface, BLUE, rect, 3, border_radius=10)
            surface.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                     rect.centery - text_surf.get_height() // 2))

        # High score
        high_score_text = FONT_MD.render(f"High Score: {self.high_score}", True, YELLOW)
        surface.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT - 100))

    def draw_level_select(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("LEVEL SELECT", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 8))

        # Calculate how many levels to show per row
        levels_per_row = 10
        level_buttons = []

        for level_num in range(1, self.max_level + 1):
            row = (level_num - 1) // levels_per_row
            col = (level_num - 1) % levels_per_row

            x_pos = WIDTH // 2 - (levels_per_row * 60) // 2 + col * 60
            y_pos = HEIGHT // 5 + row * 80

            rect = pygame.Rect(x_pos, y_pos, 50, 50)
            level_buttons.append((rect, level_num))

            # Draw level button
            if level_num <= self.unlocked_levels:
                color = (50, 150, 50)  # Unlocked level
                text_color = WHITE
            else:
                color = (100, 100, 100)  # Locked level
                text_color = (150, 150, 150)

            pygame.draw.rect(surface, color, rect, border_radius=10)
            pygame.draw.rect(surface, BLUE, rect, 2, border_radius=10)

            level_text = FONT_MD.render(str(level_num), True, text_color)
            surface.blit(level_text, (rect.centerx - level_text.get_width() // 2,
                                      rect.centery - level_text.get_height() // 2))

        # Back button
        back_rect = pygame.Rect(50, HEIGHT - 100, 200, 50)
        pygame.draw.rect(surface, (150, 50, 50), back_rect, border_radius=10)
        pygame.draw.rect(surface, RED, back_rect, 2, border_radius=10)
        back_text = FONT_MD.render("Back", True, WHITE)
        surface.blit(back_text, (back_rect.centerx - back_text.get_width() // 2,
                                 back_rect.centery - back_text.get_height() // 2))

        # Handle mouse clicks
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Check level buttons
        for rect, level_num in level_buttons:
            if rect.collidepoint(mouse_pos) and mouse_pressed and level_num <= self.unlocked_levels:
                self.level = level_num
                self.reset_game()
                self.state = GameState.PLAYING

        # Check back button
        if back_rect.collidepoint(mouse_pos) and mouse_pressed:
            self.state = GameState.START_MENU

    def draw_settings_menu(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("SETTINGS", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 8))

        # Settings options
        options = [
            (f"Sound: {'ON' if self.settings['sound'] else 'OFF'}", "sound"),
            (f"Music: {'ON' if self.settings['music'] else 'OFF'}", "music"),
            (f"Difficulty: {self.settings['difficulty'].title()}", "difficulty"),
            (f"Two Players: {'ON' if self.settings.get('two_players', False) else 'OFF'}", "two_players"),
            ("Back", "back")
        ]

        mouse_pos = pygame.mouse.get_pos()

        for i, (text, setting) in enumerate(options):
            y_pos = HEIGHT // 4 + i * 70
            text_surf = FONT_MD.render(text, True, WHITE)
            rect = pygame.Rect(WIDTH // 2 - 200, y_pos, 400, 50)

            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (50, 50, 100), rect, border_radius=10)
                if pygame.mouse.get_pressed()[0]:
                    if setting == "back":
                        self.state = GameState.START_MENU
                    elif setting in ["sound", "music", "two_players"]:
                        self.settings[setting] = not self.settings.get(setting, False)
                    elif setting == "difficulty":
                        diffs = ["easy", "normal", "hard"]
                        current = self.settings["difficulty"]
                        self.settings["difficulty"] = diffs[(diffs.index(current) + 1) % len(diffs)]
            else:
                pygame.draw.rect(surface, (30, 30, 60), rect, border_radius=10)

            pygame.draw.rect(surface, BLUE, rect, 3, border_radius=10)
            surface.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                     rect.centery - text_surf.get_height() // 2))

    def draw_tutorial(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("TUTORIAL", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 8))

        # Display tutorial text
        text = self.tutorial_text[self.tutorial_step]
        text_surf = FONT_MD.render(text, True, WHITE)
        surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, HEIGHT // 3))

        # Navigation
        nav_text = FONT_MD.render("Press SPACE to continue, ESC to skip", True, GREEN)
        surface.blit(nav_text, (WIDTH // 2 - nav_text.get_width() // 2, HEIGHT - 100))

    def draw_story(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        # Display story text
        text = self.story[self.story_index]
        text_surf = FONT_LG.render(text, True, WHITE)
        surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, HEIGHT // 3))

        # Navigation
        nav_text = FONT_MD.render("Press SPACE to continue", True, GREEN)
        surface.blit(nav_text, (WIDTH // 2 - nav_text.get_width() // 2, HEIGHT - 100))

    def draw_achievements(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("ACHIEVEMENTS", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 8))

        # Display achievements
        for i, achievement in enumerate(self.achievements):
            y_pos = HEIGHT // 5 + i * 60
            color = GREEN if achievement["unlocked"] else RED
            text = f"{achievement['name']}: {achievement['description']}"
            text_surf = FONT_MD.render(text, True, color)
            surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, y_pos))

        # Navigation
        nav_text = FONT_MD.render("Press ESC to go back", True, GREEN)
        surface.blit(nav_text, (WIDTH // 2 - nav_text.get_width() // 2, HEIGHT - 100))

    def draw_challenges(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("CHALLENGES", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 8))

        # Display challenges
        for i, challenge in enumerate(self.challenges):
            y_pos = HEIGHT // 5 + i * 70
            color = GREEN if challenge["completed"] else YELLOW
            text = f"{challenge['name']}: {challenge['description']} - Reward: {challenge['reward']} coins"
            text_surf = FONT_MD.render(text, True, color)
            surface.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, y_pos))

        # Navigation
        nav_text = FONT_MD.render("Press ESC to go back", True, GREEN)
        surface.blit(nav_text, (WIDTH // 2 - nav_text.get_width() // 2, HEIGHT - 100))

    def draw_shop(self, surface):
        surface.fill(BLACK)
        self.draw_stars(surface)

        title = FONT_XL.render("SHOP", True, YELLOW)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 8))

        # Shop items
        items = [
            ("Weapon Upgrade", f"50 × {self.player.weapon_power} coins", "upgrade_weapon"),
            ("Advanced Rocket", "200 coins", "upgrade_rocket:advanced"),
            ("Ultimate Rocket", "500 coins", "upgrade_rocket:ultimate"),
            ("Unlock Missiles", "300 coins", "unlock:missile"),
            ("Unlock Plasma Cannon", "500 coins", "unlock:plasma"),
            ("Back", "", "back")
        ]

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for i, (name, price, action) in enumerate(items):
            y_pos = HEIGHT // 4 + i * 70
            rect = pygame.Rect(WIDTH // 2 - 200, y_pos, 400, 60)

            # Check if player can afford
            can_afford = True
            if "coins" in price:
                cost = int(price.split()[0])
                can_afford = self.player.coins >= cost

            # Draw item
            if rect.collidepoint(mouse_pos) and can_afford:
                pygame.draw.rect(surface, (50, 100, 50), rect, border_radius=10)
                if mouse_pressed:
                    if action == "back":
                        self.state = GameState.PLAYING
                    elif action == "upgrade_weapon":
                        if self.player.upgrade_weapon():
                            # Successfully upgraded
                            pass
                    elif action.startswith("upgrade_rocket:"):
                        rocket_type = action.split(":")[1]
                        if self.player.upgrade_rocket(rocket_type):
                            # Successfully upgraded
                            pass
                    elif action.startswith("unlock:"):
                        weapon = action.split(":")[1]
                        if weapon == "missile":
                            if self.player.coins >= 300:
                                self.player.coins -= 300
                                self.player.unlock_weapon(weapon)
                                self.player.switch_weapon(weapon)
                        elif weapon == "plasma":
                            if self.player.coins >= 500:
                                self.player.coins -= 500
                                self.player.unlock_weapon(weapon)
                                self.player.switch_weapon(weapon)
            else:
                color = (30, 60, 30) if can_afford else (60, 30, 30)
                pygame.draw.rect(surface, color, rect, border_radius=10)

            pygame.draw.rect(surface, GREEN if can_afford else RED, rect, 3, border_radius=10)

            # Draw text
            name_text = FONT_MD.render(name, True, WHITE)
            price_text = FONT_MD.render(price, True, YELLOW if can_afford else RED)

            surface.blit(name_text, (rect.centerx - name_text.get_width() // 2, y_pos + 10))
            surface.blit(price_text, (rect.centerx - price_text.get_width() // 2, y_pos + 35))

        # Player coins
        coins_text = FONT_LG.render(f"Coins: {self.player.coins}", True, YELLOW)
        surface.blit(coins_text, (WIDTH // 2 - coins_text.get_width() // 2, HEIGHT - 100))

    def draw_pause_menu(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        title = FONT_XL.render("PAUSED", True, WHITE)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        options = [
            ("Resume", GameState.PLAYING),
            ("Shop", GameState.SHOP),
            ("Restart Level", "restart"),
            ("Main Menu", GameState.START_MENU)
        ]

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for i, (text, action) in enumerate(options):
            y_pos = HEIGHT // 3 + i * 80
            text_surf = FONT_LG.render(text, True, WHITE)
            rect = pygame.Rect(WIDTH // 2 - 150, y_pos, 300, 50)

            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (50, 50, 100), rect, border_radius=10)
                if mouse_pressed:
                    if action == "restart":
                        self.reset_level()
                    else:
                        self.state = action
            else:
                pygame.draw.rect(surface, (30, 30, 60), rect, border_radius=10)

            pygame.draw.rect(surface, BLUE, rect, 3, border_radius=10)
            surface.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                     rect.centery - text_surf.get_height() // 2))

    def draw_level_complete(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        title = FONT_XL.render(f"LEVEL {self.level} COMPLETE!", True, GREEN)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        # Calculate time taken in seconds
        time_taken = (self.level_complete_time - self.level_start_time) // 1000
        minutes = time_taken // 60
        seconds = time_taken % 60

        stats = [
            f"Score: {self.player.score}",
            f"Coins Collected: {self.level_stats['coins_collected']}",
            f"Enemies Killed: {self.level_stats['enemies_killed']}",
            f"Damage Taken: {self.level_stats['damage_taken']}",
            f"Time Taken: {minutes:02d}:{seconds:02d}"
        ]

        for i, stat in enumerate(stats):
            text = FONT_LG.render(stat, True, WHITE)
            surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3 + i * 60))

        # Draw buttons
        button_width = 200
        button_height = 60
        button_margin = 30

        # Home button
        home_rect = pygame.Rect(
            WIDTH // 2 - button_width - button_margin // 2,
            HEIGHT - 150,
            button_width,
            button_height
        )
        pygame.draw.rect(surface, (200, 50, 50), home_rect, border_radius=10)
        pygame.draw.rect(surface, RED, home_rect, 3, border_radius=10)
        home_text = FONT_MD.render("Home", True, WHITE)
        surface.blit(home_text, (home_rect.centerx - home_text.get_width() // 2,
                                 home_rect.centery - home_text.get_height() // 2))

        # Next level button
        next_rect = pygame.Rect(
            WIDTH // 2 + button_margin // 2,
            HEIGHT - 150,
            button_width,
            button_height
        )
        pygame.draw.rect(surface, (50, 200, 50), next_rect, border_radius=10)
        pygame.draw.rect(surface, GREEN, next_rect, 3, border_radius=10)
        next_text = FONT_MD.render("Next Level", True, WHITE)
        surface.blit(next_text, (next_rect.centerx - next_text.get_width() // 2,
                                 next_rect.centery - next_text.get_height() // 2))

        # Store button rects for click detection
        self.home_button = home_rect
        self.next_level_button = next_rect

    def spawn_enemy(self):
        # Determine enemy type based on level
        if self.level == 1:
            enemy_types = [EnemyType.ASTEROID] * 8 + [EnemyType.SCOUT] * 2
        elif self.level == 2:
            enemy_types = [EnemyType.ASTEROID] * 6 + [EnemyType.SCOUT] * 3 + [EnemyType.FIGHTER]
        elif self.level == 3:
            enemy_types = [EnemyType.ASTEROID] * 5 + [EnemyType.SCOUT] * 3 + [EnemyType.FIGHTER] * 2
        elif self.level == 4:
            enemy_types = [EnemyType.ASTEROID] * 4 + [EnemyType.SCOUT] * 3 + [EnemyType.FIGHTER] * 2 + [
                EnemyType.BOMBER]
        elif self.level == 5:
            enemy_types = [EnemyType.ASTEROID] * 3 + [EnemyType.SCOUT] * 2 + [EnemyType.FIGHTER] * 3 + [
                EnemyType.BOMBER] * 2
        else:  # Level 6+ or endless
            enemy_types = [EnemyType.FIGHTER] * 2 + [EnemyType.BOMBER] * 3 + [EnemyType.ELITE] * 2

        enemy_type = random.choice(enemy_types)
        return Enemy(random.randint(20, WIDTH - 40), -40, enemy_type, self.level)

    def spawn_boss(self):
        self.boss = Boss(self.level)
        self.boss_active = True

    def spawn_power_up(self, x, y, type=None):
        if not type:
            # Weighted random selection
            types = [PowerUpType.COIN] * 5 + [PowerUpType.HEALTH] * 3 + [PowerUpType.SHIELD] * 2 + [
                PowerUpType.RAPID_FIRE] * 2 + [PowerUpType.GUN] * 1
            type = random.choice(types)
        self.power_ups.append(PowerUp(x, y, type))

    def create_explosion(self, x, y, size):
        # Create visual explosion effect
        for _ in range(20):
            particle = {
                "x": x,
                "y": y,
                "dx": random.uniform(-3, 3),
                "dy": random.uniform(-3, 3),
                "size": random.randint(2, size),
                "color": (random.randint(200, 255), random.randint(100, 200), 0),
                "life": random.randint(20, 40)
            }
            self.explosions.append(particle)

        # Trigger camera shake
        self.camera_shake = 15

    def update_camera_shake(self):
        if self.camera_shake > 0:
            self.camera_offset = (random.randint(-5, 5), random.randint(-5, 5))
            self.camera_shake -= 1
        else:
            self.camera_offset = (0, 0)

    def check_achievements(self):
        # First Blood
        if not self.achievements[0]["unlocked"] and self.enemies_defeated > 0:
            self.achievements[0]["unlocked"] = True

        # Coin Collector
        if not self.achievements[1]["unlocked"] and self.player.coins >= 100:
            self.achievements[1]["unlocked"] = True

        # Boss Slayer
        if not self.achievements[2]["unlocked"] and self.level > 1:
            self.achievements[2]["unlocked"] = True

        # Weapon Master
        if not self.achievements[3]["unlocked"] and len(self.player.weapons_unlocked) == 3:
            self.achievements[3]["unlocked"] = True

        # Ultimate Pilot
        if not self.achievements[4]["unlocked"] and self.level > self.max_level:
            self.achievements[4]["unlocked"] = True

    def load_high_score(self):
        try:
            with open("high_score.json", "r") as file:
                data = json.load(file)
                self.high_score = data.get("high_score", 0)
                self.unlocked_levels = data.get("unlocked_levels", 1)
        except:
            self.high_score = 0
            self.unlocked_levels = 1

    def save_high_score(self):
        data = {
            "high_score": self.high_score,
            "unlocked_levels": self.unlocked_levels
        }
        with open("high_score.json", "w") as file:
            json.dump(data, file)

    def load_achievements(self):
        try:
            with open("achievements.json", "r") as file:
                return json.load(file)
        except:
            return []

    def save_achievements(self):
        with open("achievements.json", "w") as file:
            json.dump(self.achievements, file)

    def load_challenges(self):
        try:
            with open("challenges.json", "r") as file:
                return json.load(file)
        except:
            return []

    def save_challenges(self):
        with open("challenges.json", "w") as file:
            json.dump(self.challenges, file)

    def reset_level(self):
        self.player.rect.x = WIDTH // 2 - self.player.width // 2
        if self.player2:
            self.player2.rect.x = WIDTH // 2 + 100
        self.projectiles = []
        self.enemies = []
        self.enemy_projectiles = []
        self.power_ups = []
        self.boss = None
        self.boss_active = False
        self.player.rapid_fire = False
        self.player.shield = False
        self.camera_shake = 0
        self.camera_offset = (0, 0)
        self.explosions = []
        self.enemies_defeated = 0
        self.enemies_to_defeat = 10 + self.level * 5

        # Reset level stats
        self.level_stats = {
            "coins_collected": 0,
            "enemies_killed": 0,
            "damage_taken": 0,
            "time_taken": 0
        }

        # Set start time for level
        self.level_start_time = pygame.time.get_ticks()

        # Spawn initial enemies
        for _ in range(5 + self.level * 2):
            self.enemies.append(self.spawn_enemy())

    def reset_game(self):
        self.player = Player()
        if self.settings["two_players"]:
            self.player2 = Player(WIDTH // 2 - 100)
        else:
            self.player2 = None

        self.reset_level()
        self.state = GameState.PLAYING

        # Start with story for level 1
        if self.level == 1:
            self.state = GameState.STORY
            self.story_index = 0

    def next_level(self):
        # Unlock next level
        if self.level == self.unlocked_levels:
            self.unlocked_levels = min(self.max_level, self.unlocked_levels + 1)
            self.save_high_score()

        self.level = min(self.max_level, self.level + 1)
        self.reset_level()
        self.state = GameState.PLAYING

    def run(self):
        while True:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in [GameState.PLAYING, GameState.PAUSED]:
                            self.state = GameState.PAUSED if self.state == GameState.PLAYING else GameState.PLAYING
                        elif self.state in [GameState.TUTORIAL, GameState.SETTINGS, GameState.ACHIEVEMENTS,
                                            GameState.CHALLENGES, GameState.STORY, GameState.LEVEL_SELECT]:
                            self.state = GameState.START_MENU

                    if event.key == pygame.K_p and self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED

                    if event.key == pygame.K_SPACE:
                        if self.state == GameState.TUTORIAL:
                            self.tutorial_step += 1
                            if self.tutorial_step >= len(self.tutorial_text):
                                self.state = GameState.PLAYING
                        elif self.state == GameState.STORY:
                            self.story_index += 1
                            if self.story_index >= len(self.story):
                                self.state = GameState.PLAYING

                    if event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                        self.reset_game()

                    if event.key == pygame.K_s and self.state == GameState.PLAYING:
                        self.state = GameState.SHOP

                    # Weapon switching
                    if event.key == pygame.K_1 and self.state == GameState.PLAYING:
                        self.player.switch_weapon("laser")
                    if event.key == pygame.K_2 and self.state == GameState.PLAYING and "missile" in self.player.weapons_unlocked:
                        self.player.switch_weapon("missile")
                    if event.key == pygame.K_3 and self.state == GameState.PLAYING and "plasma" in self.player.weapons_unlocked:
                        self.player.switch_weapon("plasma")

                # Handle mouse clicks for level complete screen
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == GameState.LEVEL_COMPLETE:
                        mouse_pos = pygame.mouse.get_pos()
                        if hasattr(self, 'home_button') and self.home_button.collidepoint(mouse_pos):
                            self.state = GameState.START_MENU
                        elif hasattr(self, 'next_level_button') and self.next_level_button.collidepoint(mouse_pos):
                            self.next_level()

            # Update game state
            if self.state == GameState.PLAYING:
                # Player 1 movement
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.player.move(-self.player.speed)
                if keys[pygame.K_RIGHT]:
                    self.player.move(self.player.speed)

                # Player 2 movement
                if self.player2:
                    if keys[pygame.K_a]:
                        self.player2.move(-self.player2.speed)
                    if keys[pygame.K_d]:
                        self.player2.move(self.player2.speed)

                # Player 1 shooting
                if keys[pygame.K_SPACE] and self.player.shoot_cooldown <= 0:
                    # Determine weapon type
                    if self.player.weapon_type == "laser":
                        weapon = WeaponType.LASER
                    elif self.player.weapon_type == "missile":
                        weapon = WeaponType.MISSILE
                    elif self.player.weapon_type == "plasma":
                        weapon = WeaponType.PLASMA

                    self.projectiles.append(Projectile(
                        self.player.rect.centerx,
                        self.player.rect.top,
                        weapon,
                        self.player.weapon_power
                    ))

                    # Set cooldown based on rapid fire
                    if self.player.rapid_fire:
                        self.player.shoot_cooldown = 5  # Very fast shooting
                    else:
                        self.player.shoot_cooldown = 15  # Normal shooting

                # Shooting for player 2
                if self.player2 and keys[pygame.K_w] and self.player2.shoot_cooldown <= 0:
                    # Determine weapon type
                    if self.player2.weapon_type == "laser":
                        weapon = WeaponType.LASER
                    elif self.player2.weapon_type == "missile":
                        weapon = WeaponType.MISSILE
                    elif self.player2.weapon_type == "plasma":
                        weapon = WeaponType.PLASMA

                    self.projectiles.append(Projectile(
                        self.player2.rect.centerx,
                        self.player2.rect.top,
                        weapon,
                        self.player2.weapon_power
                    ))

                    # Set cooldown for player2
                    if self.player2.rapid_fire:
                        self.player2.shoot_cooldown = 5
                    else:
                        self.player2.shoot_cooldown = 15

                # Update player
                self.player.update()
                if self.player2:
                    self.player2.update()

                # Update camera shake
                self.update_camera_shake()

                # Update projectiles
                for proj in self.projectiles[:]:
                    proj.move()
                    if proj.rect.bottom < 0:
                        self.projectiles.remove(proj)

                # Update enemy projectiles
                for proj in self.enemy_projectiles[:]:
                    proj.rect.y += proj.speed
                    if proj.rect.top > HEIGHT:
                        self.enemy_projectiles.remove(proj)
                    # Check collision with player
                    if proj.rect.colliderect(self.player.rect):
                        if self.player.take_damage(proj.damage):
                            self.create_explosion(proj.rect.centerx, proj.rect.centery, 10)
                            self.level_stats['damage_taken'] += proj.damage
                        self.enemy_projectiles.remove(proj)
                        if self.player.health <= 0:
                            self.state = GameState.GAME_OVER

                    # Check collision with player2
                    if self.player2 and proj.rect.colliderect(self.player2.rect):
                        if self.player2.take_damage(proj.damage):
                            self.create_explosion(proj.rect.centerx, proj.rect.centery, 10)
                            self.level_stats['damage_taken'] += proj.damage
                        self.enemy_projectiles.remove(proj)
                        if self.player2.health <= 0:
                            self.state = GameState.GAME_OVER

                # Update enemies
                for enemy in self.enemies[:]:
                    enemy.move()
                    enemy.update_cooldown()

                    # Enemy shooting
                    if enemy.can_shoot():
                        self.enemy_projectiles.append(Projectile(
                            enemy.rect.centerx,
                            enemy.rect.bottom,
                            WeaponType.LASER,
                            1
                        ))
                        enemy.reset_cooldown()

                    # Enemy collision with player
                    if enemy.rect.colliderect(self.player.rect):
                        if self.player.take_damage(10):
                            self.create_explosion(enemy.rect.centerx, enemy.rect.centery, 20)
                            self.level_stats['damage_taken'] += 10
                        self.enemies.remove(enemy)
                        self.enemies_defeated += 1
                        self.level_stats['enemies_killed'] += 1
                        if self.player.health <= 0:
                            self.state = GameState.GAME_OVER

                    # Enemy collision with player2
                    if self.player2 and enemy.rect.colliderect(self.player2.rect):
                        if self.player2.take_damage(10):
                            self.create_explosion(enemy.rect.centerx, enemy.rect.centery, 20)
                            self.level_stats['damage_taken'] += 10
                        self.enemies.remove(enemy)
                        self.enemies_defeated += 1
                        self.level_stats['enemies_killed'] += 1
                        if self.player2.health <= 0:
                            self.state = GameState.GAME_OVER

                    # Remove enemies that go off screen
                    if enemy.rect.top > HEIGHT:
                        self.enemies.remove(enemy)

                # Update boss
                if self.boss_active:
                    self.boss.move()
                    self.boss.update_cooldown()
                    self.boss.update_shield()

                    # Boss shooting
                    if self.boss.can_shoot():
                        # Pattern 1: Triple shot
                        if self.boss.attack_pattern == 0:
                            for offset in [-40, 0, 40]:
                                self.enemy_projectiles.append(Projectile(
                                    self.boss.rect.centerx + offset,
                                    self.boss.rect.bottom,
                                    WeaponType.LASER,
                                    3
                                ))
                            self.boss.attack_timer = 60
                            self.boss.attack_pattern = 1
                        # Pattern 2: Moving shield
                        elif self.boss.attack_pattern == 1:
                            self.boss.activate_shield()
                            self.boss.attack_timer = 120
                            self.boss.attack_pattern = 0
                        self.boss.reset_cooldown()

                    # Boss collision with player
                    if self.boss.rect.colliderect(self.player.rect):
                        if self.player.take_damage(20):
                            self.create_explosion(self.boss.rect.centerx, self.boss.rect.centery, 30)
                            self.level_stats['damage_taken'] += 20
                        if self.player.health <= 0:
                            self.state = GameState.GAME_OVER

                    # Boss collision with player2
                    if self.player2 and self.boss.rect.colliderect(self.player2.rect):
                        if self.player2.take_damage(20):
                            self.create_explosion(self.boss.rect.centerx, self.boss.rect.centery, 30)
                            self.level_stats['damage_taken'] += 20
                        if self.player2.health <= 0:
                            self.state = GameState.GAME_OVER

                    # Check if boss is defeated
                    if self.boss.health <= 0:
                        self.player.add_coins(self.boss.value)
                        self.player.score += self.boss.value * 10
                        self.level_stats['coins_collected'] += self.boss.value
                        self.create_explosion(self.boss.rect.centerx, self.boss.rect.centery, 50)
                        self.boss_active = False
                        self.level_complete_time = pygame.time.get_ticks()
                        self.state = GameState.LEVEL_COMPLETE

                # Check collisions between player projectiles and enemies
                for proj in self.projectiles[:]:
                    # Check enemy collisions
                    for enemy in self.enemies[:]:
                        if proj.rect.colliderect(enemy.rect):
                            enemy.health -= proj.damage
                            if enemy.health <= 0:
                                self.player.score += enemy.value
                                self.player.add_coins(enemy.value)
                                self.level_stats['coins_collected'] += enemy.value
                                self.enemies_defeated += 1
                                self.level_stats['enemies_killed'] += 1

                                # Chance to drop power-up
                                if random.random() < enemy.drop_chance:
                                    self.spawn_power_up(enemy.rect.centerx, enemy.rect.centery)

                                self.enemies.remove(enemy)

                            # Create explosion
                            self.create_explosion(proj.rect.centerx, proj.rect.centery, 15)

                            # Remove projectile
                            if proj in self.projectiles:
                                self.projectiles.remove(proj)
                            break

                    # Check boss collision
                    if self.boss_active and proj.rect.colliderect(self.boss.rect):
                        if self.boss.take_damage(proj.damage):
                            self.create_explosion(proj.rect.centerx, proj.rect.centery, 20)
                        if proj in self.projectiles:
                            self.projectiles.remove(proj)

                # Update power-ups
                for power in self.power_ups[:]:
                    power.move()

                    # Power-up collision with player
                    if power.rect.colliderect(self.player.rect):
                        if power.type == PowerUpType.COIN:
                            self.player.add_coins(5)
                            self.level_stats['coins_collected'] += 5
                        elif power.type == PowerUpType.HEALTH:
                            self.player.heal(20)
                        elif power.type == PowerUpType.RAPID_FIRE:
                            self.player.rapid_fire = True
                            self.player.rapid_fire_timer = 300
                        elif power.type == PowerUpType.SHIELD:
                            self.player.activate_shield()
                        elif power.type == PowerUpType.GUN:
                            if "missile" not in self.player.weapons_unlocked:
                                self.player.unlock_weapon("missile")
                            elif "plasma" not in self.player.weapons_unlocked:
                                self.player.unlock_weapon("plasma")
                        self.power_ups.remove(power)

                    # Power-up collision with player2
                    if self.player2 and power.rect.colliderect(self.player2.rect):
                        if power.type == PowerUpType.COIN:
                            self.player.add_coins(5)  # Only one coin counter
                            self.level_stats['coins_collected'] += 5
                        elif power.type == PowerUpType.HEALTH:
                            self.player2.heal(20)
                        elif power.type == PowerUpType.RAPID_FIRE:
                            self.player2.rapid_fire = True
                            self.player2.rapid_fire_timer = 300
                        elif power.type == PowerUpType.SHIELD:
                            self.player2.activate_shield()
                        elif power.type == PowerUpType.GUN:
                            if "missile" not in self.player2.weapons_unlocked:
                                self.player2.unlock_weapon("missile")
                            elif "plasma" not in self.player2.weapons_unlocked:
                                self.player2.unlock_weapon("plasma")
                        if power in self.power_ups:
                            self.power_ups.remove(power)

                    # Remove power-ups that go off screen
                    if power.rect.top > HEIGHT:
                        self.power_ups.remove(power)

                # Spawn new enemies
                if len(self.enemies) < 5 + self.level and random.random() < 0.02:
                    self.enemies.append(self.spawn_enemy())

                # Spawn boss when enemies are cleared
                if not self.boss_active and self.enemies_defeated >= self.enemies_to_defeat:
                    self.enemies = []  # Clear existing enemies
                    self.spawn_boss()

                # Update explosions
                for explosion in self.explosions[:]:
                    explosion["x"] += explosion["dx"]
                    explosion["y"] += explosion["dy"]
                    explosion["life"] -= 1
                    if explosion["life"] <= 0:
                        self.explosions.remove(explosion)

            # Drawing
            win.fill(BLACK)

            # Apply camera offset
            offset_surface = pygame.Surface((WIDTH, HEIGHT))
            offset_surface.fill(BLACK)

            # Draw stars
            self.draw_stars(offset_surface)

            # Draw game elements based on state
            if self.state == GameState.PLAYING:
                # Draw player
                self.player.draw(offset_surface)
                if self.player2:
                    self.player2.draw(offset_surface)

                # Draw projectiles
                for proj in self.projectiles:
                    proj.draw(offset_surface)

                # Draw enemy projectiles
                for proj in self.enemy_projectiles:
                    proj.draw(offset_surface)

                # Draw enemies
                for enemy in self.enemies:
                    enemy.draw(offset_surface)

                # Draw boss
                if self.boss_active:
                    self.boss.draw(offset_surface)

                # Draw power-ups
                for power in self.power_ups:
                    power.draw(offset_surface)

                # Draw explosions
                for explosion in self.explosions:
                    pygame.draw.circle(offset_surface, explosion["color"],
                                       (int(explosion["x"]), int(explosion["y"])),
                                       explosion["size"])

                # Draw UI
                self.draw_ui(offset_surface)

            elif self.state == GameState.START_MENU:
                self.draw_start_menu(offset_surface)

            elif self.state == GameState.LEVEL_SELECT:
                self.draw_level_select(offset_surface)

            elif self.state == GameState.SETTINGS:
                self.draw_settings_menu(offset_surface)

            elif self.state == GameState.TUTORIAL:
                self.draw_tutorial(offset_surface)

            elif self.state == GameState.GAME_OVER:
                self.draw_game_over(offset_surface)

            elif self.state == GameState.SHOP:
                self.draw_shop(offset_surface)

            elif self.state == GameState.PAUSED:
                self.draw_pause_menu(offset_surface)

            elif self.state == GameState.LEVEL_COMPLETE:
                self.draw_level_complete(offset_surface)

            elif self.state == GameState.STORY:
                self.draw_story(offset_surface)

            elif self.state == GameState.ACHIEVEMENTS:
                self.draw_achievements(offset_surface)

            elif self.state == GameState.CHALLENGES:
                self.draw_challenges(offset_surface)

            # Apply camera offset to the whole screen
            win.blit(offset_surface, self.camera_offset)

            pygame.display.flip()
            self.clock.tick(60)


# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()





















