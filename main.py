import pygame

import constants as c
import frame as f
import sys
from sound_manager import SoundManager
from image_manager import ImageManager
import asyncio

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.set_num_channels(12)
        SoundManager.init()
        ImageManager.init()
        self.screen = pygame.display.set_mode(c.WINDOW_SIZE)
        pygame.display.set_caption(c.CAPTION)
        self.clock = pygame.time.Clock()
        self.windowed = False
        self.clicked = False
        self.paused = False
        self.points = 0
        asyncio.run(self.main())

    async def main(self):
        current_frame = f.GameFrame(self)
        current_frame.load()
        self.clock.tick(60)

        try:
            pygame.mouse.set_cursor((13,13),ImageManager.load("assets/images/crosshairs.png"))
        except:
            pass

        while True:
            dt, events = self.get_events()
            await asyncio.sleep(0)
            if not self.paused:
                if dt == 0:
                    dt = 1/100000
                pygame.display.set_caption(f"{c.CAPTION} ({int(1/dt)} FPS)")
                if dt > 0.05:
                    dt = 0.05

                current_frame.update(dt, events)
                current_frame.draw(self.screen, (0, 0))
                self.points = 10* current_frame.zombies_killed
                self.instruction()
                self.draw_points()
                pygame.display.flip()

                if current_frame.done:
                    current_frame = current_frame.next_frame()
                    current_frame.load()
            else:
                pygame.display.set_caption(f"{c.CAPTION} (Paused)")
                self.draw_pause_menu() 
                pygame.display.flip()

    def instruction(self):
        font = pygame.font.Font(None, 22)
        text = font.render("Press q to pause", True, (255,255,255))
        text_rect = text.get_rect(topright=(c.WINDOW_SIZE[0] -10, 10))
        self.screen.blit(text, text_rect)

        text2 = font.render("Press s to skip current line when on phone", True, (255,255,255))
        text2_rect = text2.get_rect(topright=(c.WINDOW_SIZE[0] -10, 30))
        self.screen.blit(text2, text2_rect)

    def draw_pause_menu(self):
        font = pygame.font.Font(None, 48)
        text = font.render("Paused game, press q again to resume", True, (255,255,255))
        text_rect = text.get_rect(center=(c.WINDOW_SIZE[0]//2, c.WINDOW_SIZE[1]//2))
        self.screen.blit(text, text_rect)

    def get_events(self):
        dt = self.clock.tick(c.FRAMERATE)/1000

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_q:
                    self.paused = not self.paused

        pressed = pygame.mouse.get_pressed()
        try:
            if pressed[0] and not self.clicked:
                self.clicked = True
                pygame.mouse.set_cursor((12, 12), ImageManager.load("assets/images/small_cursor.png"))
            elif not pressed[0] and self.clicked:
                self.clicked = False
                pygame.mouse.set_cursor((12, 12), ImageManager.load("assets/images/crosshairs.png"))
        except:
            pass

        return dt, events
    def draw_points(self):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Points: {self.points}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(c.WINDOW_SIZE[0] // 2,50))
        self.screen.blit(text, text_rect)

if __name__=="__main__":
    Game()
