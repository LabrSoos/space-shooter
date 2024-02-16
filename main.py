import pygame
import random
import pickle

pygame.init()

WIDTH = 1200
HEIGHT = 676
TICKRATE = 60
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
VIOLET = (72, 45, 135)
VIOLET_HOVER = (85, 55, 155)
TEAL = (55, 180, 180)
BLACK = (0, 0, 0)
bg = pygame.image.load('assets/kosmos_fon.png')

window = pygame.display.set_mode((WIDTH, HEIGHT))

clock = pygame.time.Clock()

class SpaceShip(pygame.sprite.Sprite):
    def __init__(self, x, y, image, speed, shoot_cd, hp, volume = 0.05):
        super().__init__()
        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect(center = (x, y))
        self.speed = speed
        self.shoot_cd = CoolDown(shoot_cd)
        self.base_hp = hp
        self.hp = hp
        self.laser_sound = pygame.mixer.Sound('assets/laser.mp3')
        self.laser_sound.set_volume(volume)

    def draw(self):
        window.blit(self.image, self.rect)

    def destroy(self):
        self.hp = 1
        self.get_damage()

class Player(SpaceShip): 
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.rect.y -= self.speed

        if keys[pygame.K_s]:
            self.rect.y += self.speed

        if keys[pygame.K_a]:
           self.rect.x -= self.speed

        if keys[pygame.K_d]:
            self.rect.x += self.speed

        if self.rect.top < 0:
            self.rect.top = 0

        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

        if self.rect.left < 0:
            self.rect.left = 0

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH


        if self.shoot_cd.done(False):
            if keys[pygame.K_SPACE]:
                self.laser_sound.play()
                self.shoot_cd.reset()
                game.play.player_lasers.add(Laser(
                    self.rect.left,
                    self.rect.centery,
                    BLUE,
                    -5
                ))
                game.play.player_lasers.add(Laser(
                    self.rect.right,
                    self.rect.centery,
                    BLUE,
                    -5
                ))

        collided_enemy = pygame.sprite.spritecollideany(self, game.play.enemies)

        if collided_enemy:
            self.destroy()
            collided_enemy.destroy()

        collided_laser = pygame.sprite.spritecollideany(self, game.play.enemy_lasers)

        if collided_laser:
            self.get_damage()
            collided_laser.kill()

    def get_damage(self):
        if self.hp > 0:
            self.hp -= 1
            game.hud.hp_bar.update()
            if self.hp == 0:
                game.play.explosions.add(Explosion(*self.rect.center, self.game_over))

    def game_over(self):
        game.change_state('over')

    def draw(self):
        if self.hp > 0:
            super().draw()

class Enemy(SpaceShip):
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
        collided_laser = pygame.sprite.spritecollideany(self, game.play.player_lasers)
        if collided_laser:
            collided_laser.kill()
            self.get_damage()
        if self.shoot_cd.done():
            self.laser_sound.play()
            game.play.enemy_lasers.add(Laser(
                self.rect.centerx,
                self.rect.bottom,
                RED,
                5
            ))

    def get_damage(self):
        self.hp -= 1
        if self.hp == 0:
            self.kill()
            game.score += 1
            game.hud.score.change(str(game.score))
            game.play.explosions.add(Explosion(*self.rect.center))
            
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, callback = None):
        super().__init__()
        self.callback = callback
        self.frames_count = 12
        self.frame_index = 0
        self.frame_cd = CoolDown(TICKRATE // 10)
        image = pygame.image.load('assets/Explosion.png')
        frame_width = image.get_width() // self.frames_count
        frame_height = image.get_height()
        self.rect = (x - frame_width // 2, y - frame_height // 2)
        self.frames = []
        for i in range(self.frames_count):
            self.frames.append(image.subsurface((i * frame_width, 0 , frame_width, frame_height)))
        self.image = self.frames[0]
        sound = pygame.mixer.Sound('assets/explosion_music.wav')
        sound.set_volume(0.1)
        sound.play()

    def update(self):
        if self.frame_cd.done():
            self.frame_index += 1
            if self.frame_index == self.frames_count:
                self.kill()
                if self.callback:
                    self.callback()
            else:
                self.image = self.frames[self.frame_index] 

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed):
        super().__init__()
        self.image = pygame.Surface((3, 15))
        self.image.fill(color)
        self.rect = self.image.get_rect(center = (x, y))
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()
        


class CoolDown():
    def __init__(self, ticks):
        self.ticks = ticks
        self.current = ticks

    def reset(self):
        self.current = self.ticks

    def done(self, need_reset = True):
        if self.current == 0:
            if need_reset:
                self.reset()
            return True
        else:
            self.current -= 1
            return False

class Text():
    def __init__(self, text, size, x, y, color = WHITE):
        self.font = pygame.font.Font('assets/better-vcr-5.4.ttf', size)
        self.text = self.font.render(text, True, color)
        self.rect = self.text.get_rect(center = (x, y))
        self.color = color

    def draw(self):
        window.blit(self.text, self.rect)

    def change(self, text):
        self.text = self.font.render(text, True, self.color)

class Button():
    def __init__(self, text, x, y):
        self.hovered = False
        self.text = Text(text, 30, x, y, TEAL)
        self.bg = pygame.Surface((self.text.text.get_width() + 20, self.text.text.get_height() + 10))
        self.bg.fill(VIOLET)
        self.rect = self.bg.get_rect(center = (x, y))

    def draw(self):
        window.blit(self.bg, self.rect)
        self.text.draw()

    def hover(self, events):
        for e in events:
            if e.type == pygame.MOUSEMOTION:
                self.hovered = self.rect.collidepoint(*e.pos)

    def update(self, events):
        self.hover(events)
        if self.hovered:
            self.bg.fill(VIOLET_HOVER)
        else:
            self.bg.fill(VIOLET)
        
    def on_click(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                return self.rect.collidepoint(*e.pos)

class HPBar():
    def __init__(self):
        self.bg = pygame.Surface((150, 10))
        self.bg.fill(BLACK)
        self.hp = pygame.Surface((150, 10))
        self.hp.fill(RED)
        self.rect = self.bg.get_rect(bottomleft = (20, HEIGHT - 20))
    def draw(self):
        window.blit(self.bg, self.rect)
        window.blit(self.hp, self.rect)
    def update(self):
        size = game.play.player.hp * 30
        self.hp = pygame.Surface((size, 10))
        self.hp.fill(RED)

class HUD():
    def __init__(self):
        self.over_msg = Text('Нажмите пробел чтобы начать заново', 30, WIDTH // 2, HEIGHT // 2)
        self.score = Text('0', 25, 40, 40) 
        self.hp_bar = HPBar()

class GameManager():
    def __init__(self):
        self.state = 'menu'
        self.play = Gameplay()
        self.over = GameOver()
        self.menu = GameMenu()
        self.hud =  HUD()
        self.score = 0
        self.possible_states = ['play', 'over', 'menu']
        pygame.mixer.music.load('assets/music.mp3')
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play()
        pygame.mixer.music.pause()

    def update(self, events):
        if self.state == 'play':
            self.play.update()
            self.play.draw()

        elif self.state == 'over':
            self.over.update()
            self.play.draw()
            self.over.draw()

        elif self.state == 'menu':
            self.menu.update(events)
            self.menu.draw()

    def change_state(self, state: str):
        if state in self.possible_states:
            self.state = state
            if state == 'play':
                pygame.mixer.music.unpause()
            elif state == 'menu':
                pygame.mixer.music.pause()

    def run(self):
        while True:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    quit()

                if e.type == pygame.KEYDOWN:
                    if self.state == 'over' and e.key == pygame.K_SPACE:
                        self.__init__() 
                        self.change_state('play')
                    if e.key == pygame.K_ESCAPE:
                        self.change_state('menu') 

            self.update(events)

            pygame.display.flip()
            clock.tick(TICKRATE)

class GameMenu():
    def __init__(self):
        self.bg = pygame.transform.scale(pygame.image.load('assets/kosmos2.jpg'), (WIDTH, HEIGHT))
        self.btns = {}
        for i, btn in enumerate(['Играть', 'Рекорды', 'Выход']):
            self.btns[btn] = Button(btn, WIDTH // 2, HEIGHT // 4 * (i + 1))
    def draw(self):
        window.blit(self.bg, (0, 0))
        for btn in self.btns:
            self.btns[btn].draw()

    def update(self, events):
        for btn_name in self.btns:
            btn = self.btns[btn_name]
            btn.update(events)
            if btn.on_click(events):
                if btn_name == 'Играть':
                    game.change_state('play' if game.play.player.hp > 0 else 'over')
                elif btn_name == 'Выход':
                    exit()


class Gameplay():
    def __init__(self):

        self.player = Player(WIDTH // 2, HEIGHT // 2, 'assets/spaceship1.png', 5, TICKRATE // 2, 5, 0.2)
        self.enemies = pygame.sprite.Group()
        self.enemy_spawn = CoolDown(TICKRATE * 2)
        self.player_lasers = pygame.sprite.Group()
        self.enemy_lasers = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()


    def update(self):
        self.player.update()
        self.enemies.update()
        self.player_lasers.update()
        self.enemy_lasers.update()
        self.explosions.update()
        if self.enemy_spawn.done():
            enemy_type = random.randint(1, 23)
            if enemy_type <= 20:
                self.enemies.add(Enemy(
                    random.randint(50, WIDTH - 50), 
                    -100,
                    'assets/spaceship2.png',
                    1,
                    TICKRATE * 1.5,
                    1
                ))

            if enemy_type == 21 or enemy_type == 22:
                self.enemies.add(Enemy(
                    random.randint(50, WIDTH - 50), 
                    -100,
                    'assets/spaceship3.png',
                    1,
                    TICKRATE * 2,
                    3
                ))

            if enemy_type == 23:
                self.enemies.add(Enemy(
                    random.randint(50, WIDTH - 50), 
                    -100,
                    'assets/spaceship4.png',
                    1,
                    TICKRATE * 0.7,
                    1
                ))



    def draw(self):
        window.blit(bg, (0, 0))
        self.player.draw()
        self.enemies.draw(window)
        self.player_lasers.draw(window)
        self.enemy_lasers.draw(window)
        self.explosions.draw(window)
        game.hud.score.draw()
        game.hud.hp_bar.draw()

class GameOver():
    def __init__(self):
        pass

    def draw(self):
        game.hud.over_msg.draw()

    def update(self):
        pass

class Records():
    def __init__(self):
        file = open('records.pickle', 'rb')
        try:
            self.records = pickle.load(file)
        except:
            file.close()
            file = open('records.pickle', 'wb')
            self.records = [['-', '-'] for i in range(5)]
            pickle.dump(self.records)
        self.labels = pygame.sprite.Group()
        for row in self.records:
            ...


game = GameManager()
game.run()