import time

import pygame

from background import Background
from camera import Camera
from delivery_menu import DeliveryMenu
from enemy import Enemy, FastEnemy
from gary import Gary
from image_manager import ImageManager
from phone import Phone
from player import Player
import random
import constants as c
from primitives import Pose


class Frame:
    def __init__(self, game):
        self.game = game
        self.done = False

    def load(self):
        pass

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        surface.fill((0, 0, 0))

    def next_frame(self):
        return Frame(self.game)


class GameFrame(Frame):
    def __init__(self, game):
        super().__init__(game)
        pygame.mixer.set_num_channels(20)
        self.player = Player(self)
        self.bullets = []
        self.particles = []
        self.enemies = [Enemy(self, position=(random.random()*c.WINDOW_WIDTH, random.random()*c.WINDOW_HEIGHT)) for i in range(0)]
        Camera.init(self.player.position.get_position())
        self.vignette = ImageManager.load("assets/images/vignette.png")
        self.background = Background()
        self.phone = Phone(self, (128,0))
        Camera.snap_to_target()
        self.gary = Gary(self)
        self.hud = ImageManager.load("assets/images/hud.png")

        self.zombies_killed = 0
        self.bullets_fired = 0
        self.time_on_hold = 0

        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))
        self.black_alpha = 255
        self.black_target_alpha = 0
        self.game_over = False

        self.game_over_text_surf = ImageManager.load("assets/images/game_over.png")
        self.game_over_full_surf = None
        self.game_over_alpha = 0
        self.game_over_target_alpha = 0

        self.spawn_intensity = 0

        self.since_goomba = 0

        self.delivery = DeliveryMenu(self)

        self.music = pygame.mixer.Sound("assets/sound/please_hold.ogg")
        self.music.set_volume(0)
        self.music.play(-1)
        self.music_volume = 0
        self.full_music = pygame.mixer.Sound("assets/sound/please_hold_full.ogg")
        self.full_music.play(-1)
        self.full_music.set_volume(0)
        self.target_music_volume = 0
        self.groove = pygame.mixer.Sound("assets/sound/groove.ogg")
        self.groove.set_volume(0.07)
        self.groove.play(-1)

        self.ammo_font = pygame.font.Font("assets/fonts/RPGSystem.ttf", 30)
        self.ammo_chars = {char:self.ammo_font.render(char, 0, (255, 255, 255)) for char in "1234567890.-,∞"}

    def spawn_goomba(self, elite_chance=0.12):
        elite = False
        if self.spawn_intensity >= 2:
            elite = random.random()<elite_chance
        okay = False
        while not okay:
            x = random.random()*c.ARENA_WIDTH - c.ARENA_WIDTH//2
            y = random.random()*c.ARENA_HEIGHT - c.ARENA_HEIGHT//2
            pos = Pose((x, y))
            diff = pos - self.player.position
            if diff.magnitude() > 256:
                okay = True
        if not elite:
            new_enemy = Enemy(self, pos.get_position())
        else:
            new_enemy = FastEnemy(self, pos.get_position())
        self.enemies.append(new_enemy)
        self.enemies.sort(key=lambda each: each.position.y)
        self.since_goomba = 0

    def update_enemy_spawning(self, dt, events):
        self.since_goomba += dt
        if self.game_over:
            return
        if self.since_goomba > 3 and self.spawn_intensity == 1:
            self.spawn_goomba()
        elif self.since_goomba > 2.3 and self.spawn_intensity == 2:
            self.spawn_goomba()
        elif self.since_goomba > 15 and self.spawn_intensity == 3:
            num = min(10, (40 - len(self.enemies)))
            for i in range(num):
                self.spawn_goomba()
        elif self.spawn_intensity > 0 and self.since_goomba > 5/self.spawn_intensity and self.spawn_intensity >= 5:
            self.spawn_goomba(0.3)
            self.spawn_intensity += 0.5



    def player_died(self):
        self.game_over = True
        self.black_target_alpha = 180
        self.game_over_full_surf = self.get_game_over_surf()
        self.game_over_target_alpha = 255

    def next_frame(self):
        self.music.fadeout(200)
        self.groove.fadeout(200)
        self.full_music.fadeout(200)
        return GameFrame(self.game)

    def collideables(self):
        return [self.player] + self.enemies + [self.phone]

    def get_game_over_surf(self):
        surf = pygame.Surface(c.WINDOW_SIZE)
        surf.fill((255, 255, 0))
        surf.set_colorkey((255, 255, 0))
        surf.blit(self.game_over_text_surf, (surf.get_width()//2 - self.game_over_text_surf.get_width()//2, 235),special_flags=pygame.BLEND_ADD)

        self.points = 10 * self.zombies_killed

        zombies_text = self.gary.dialog_font.render(f"Zombies killed: {self.zombies_killed}",0,(255, 255, 255))
        surf.blit(zombies_text, (surf.get_width()//2 - zombies_text.get_width()//2, 300))
        bullets_text = self.gary.dialog_font.render(f"Bullets fired: {self.bullets_fired}", 0, (255, 255, 255))
        surf.blit(bullets_text, (surf.get_width() // 2 - bullets_text.get_width() // 2, 330))
        on_hold_text = self.gary.dialog_font.render(f"Seconds on hold: {int(self.time_on_hold)}",0,(255, 255, 255))
        surf.blit(on_hold_text, (surf.get_width()//2 - on_hold_text.get_width()//2, 360))
        points_text = self.gary.dialog_font.render(f"Points earned: {self.points}",0,(255, 255, 255))
        surf.blit(points_text, (surf.get_width()//2 - points_text.get_width()//2, 390))
        return surf

    def update(self, dt, events):
        self.delivery.update(dt, events)
        Camera.set_target(self.player.camera_target())
        Camera.update(dt, events)
        self.gary.update(dt, events)
        if self.delivery.blocking():
            dt = 0.00001

        self.update_enemy_spawning(dt, events)
        agents = [self.player] + self.enemies
        agents.sort(key=lambda agent: agent.position.y)
        for bullet in self.bullets[:]:
            bullet.update(dt, events)
            if bullet.destroyed:
                self.bullets.remove(bullet)
        for agent in agents[:]:
            agent.update(dt, events)
            if agent.destroyed:
                self.enemies.remove(agent)
        for particle in self.particles[:]:
            particle.update(dt, events)
        self.phone.update(dt, events)

        if self.black_alpha <= self.black_target_alpha:
            self.black_alpha += 250*dt
            if self.black_alpha > self.black_target_alpha:
                self.black_alpha = self.black_target_alpha
                if self.black_alpha == 255:
                    self.done = True
        else:
            self.black_alpha -= 800*dt
            if self.black_alpha < self.black_target_alpha:
                self.black_alpha = self.black_target_alpha

        if self.game_over_alpha <= self.game_over_target_alpha:
            self.game_over_alpha += 250*dt
            if self.game_over_alpha > self.game_over_target_alpha:
                self.game_over_alpha = self.game_over_target_alpha
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_over_alpha >= 255:
                        self.game_over_target_alpha = 0
                        self.black_target_alpha = 255
                if event.key == pygame.K_p:
                    self.get_delivery()
        else:
            self.game_over_alpha -= 1000*dt
            if self.game_over_alpha < self.game_over_target_alpha:
                self.game_over_alpha = self.game_over_target_alpha

        self.background.update(dt, events)



        if self.music_volume < self.target_music_volume:
            self.music_volume += dt*4
            if self.music_volume > self.target_music_volume:
                self.music_volume = self.target_music_volume
        if self.music_volume > self.target_music_volume:
            self.music_volume -= dt*5
            if self.music_volume < self.target_music_volume:
                self.music_volume = self.target_music_volume
        self.music.set_volume(self.music_volume)
        full_music_target = max(self.delivery.lowered, self.gary.showing)
        self.full_music.set_volume(0.7*min(1 - self.music_volume, full_music_target))
        self.groove.set_volume(max(0, (1 - self.music_volume - full_music_target)*0.07))

    def get_delivery(self):
        if not self.delivery.blocking():
            self.delivery.lower()

    def draw(self, surface, offset=(0, 0)):
        #surface.fill((0, 0, 0))


        agents = [self.player] + self.enemies + [self.phone]
        agents.sort(key=lambda agent: agent.position.y)

        offset = (Pose(offset) + Camera.get_draw_offset()).get_position()

        self.background.draw(surface, offset)
        for particle in self.particles:
            if particle.layer == c.BACKGROUND:
                particle.draw(surface, offset)
        if self.player.rolling:
            agents.remove(self.player)
            agents.append(self.player)
        for agent in agents:
            agent.draw_shadow(surface, offset)
        for agent in agents:
            agent.draw(surface, offset)
        for particle in self.particles:
            if particle.layer == c.FOREGROUND:
                particle.draw(surface, offset)
        for bullet in self.bullets:
            bullet.draw(surface, offset)
        surface.blit(self.vignette, (0, 0))
        if self.gary.showing > 0:
            self.gary.draw(surface, offset)

        self.draw_hud(surface, offset)

        self.delivery.draw(surface, offset)

        if self.black_alpha > 0:
            self.black.set_alpha(self.black_alpha)
            surface.blit(self.black, (0, 0))
        if self.game_over_alpha > 0 and self.game_over_full_surf:
            self.game_over_full_surf.set_alpha(self.game_over_alpha)
            surface.blit(self.game_over_full_surf, (0, 0))
            if self.game_over_alpha == 255:
                if time.time()%1<0.75:
                    surf = ImageManager.load("assets/images/spacebar.png")
                    x = surface.get_width()//2 - surf.get_width()//2
                    y = surface.get_height() - surf.get_height() - 25
                    surface.blit(surf, (x, y))

    def draw_hud(self, surface, offset=(0, 0)):
        surface.blit(self.hud, (0 ,0))

        ammo_str = str(self.player.ammo)
        if self.player.infinite_ammo:
            ammo_str="99999999999999999999999999999999999999999999999999999999999999"
        x = 40
        y = 45
        for char in ammo_str:
            char_surf = self.ammo_chars[char]
            surface.blit(char_surf, (x, y))
            x += char_surf.get_width()

        x = 16
        y = 78
        for i in range(self.player.health):
            heart = ImageManager.load("assets/images/heart.png")
            surface.blit(heart, (x, y))
            x += heart.get_width() + 2
