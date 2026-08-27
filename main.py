from kivymd.app import MDApp
from kivy.uix.image import Image
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import sp, dp
from kivy import platform
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import NoTransition
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.fitimage import FitImage
from random import randint, choice

Builder.load_file('menu.kv')
Builder.load_file('game.kv')
Builder.load_file('game_over.kv')
Builder.load_file('game_win.kv')

class Shot(Image):
    pass

class Asteroid(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'assets/image/asteroid-animated.png'
        self.fit_mode = 'fill'
        self.anim_delay = 1 / 20
        self.size_hint = (0.05, 0.1)
    
class Enemy(Image):
    enemy_hp = NumericProperty(5)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'assets/image/ship/space-ship-idle-enemy_apng.png'
        self.fit_mode = 'fill'
        self.anim_delay = 1 / 8
        self.size_hint = (0.15, 0.15)
        self.shot_timer = 0

class MoveStar(MDFloatLayout):
    def __init__(self, source, speed=dp(1), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = speed
        self.add_widget(FitImage(source=source))
        self.add_widget(FitImage(source=source, pos=(Window.width, 0)))
    def move(self):
        for img in self.children:
            img.x -= self.speed
            if img.right <= 0:
                img.x = max(child.right for child in self.children)
                
class MovePlanet(MDFloatLayout):
    def __init__(self, source, speed=dp(1), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = speed
        self.add_widget(FitImage(source=source, size_hint=(1, 1)))
    def move(self):
        for img in self.children:
            img.x -= self.speed
            if img.right <= 0:
                img.x = Window.width + randint(200, 600)

class MenuScreen(MDScreen):
    app = MDApp.get_running_app()
    
    def on_enter(self, *args):
        self.ids.bg_menu.anim_delay = 1 / 2
    
    def show_settings(self):
        self.ids.blocker.size_hint = (1, 1)
        self.ids.blocker.opacity = 1
        
        self.ids.settings_panel.size_hint = (0.4, 0.6)
        self.ids.settings_panel.opacity = 1
        
    
    def hide_settings(self):
        self.ids.blocker.size_hint = (0, 0)
        self.ids.blocker.opacity = 0
                
        self.ids.settings_panel.size_hint = (0, 0)
        self.ids.settings_panel.opacity = 0
        
    def save_settings(self):
        app = MDApp.get_running_app()
        app.store.put(
            'save_settings',
            music=self.ids.music_checkbox.active,
            sound=self.ids.soundeffect_checkbox.active,
            volume=self.ids.volume_slider.value,
            vibration=self.ids.vibration_checkbox.active,
            brightness=self.ids.brightness_slider.value
        )
    
    def reset_settings(self):
        self.ids.music_checkbox.active = True
        self.ids.soundeffect_checkbox.active = True
        self.ids.volume_slider.value = 20
        self.ids.vibration_checkbox.active = True
        self.ids.brightness_slider.value = 100
        
    def bg_music(self, value):
        app.music_enabled = value
        app.win_enabled = value
        if value:
            if self.manager.current != 'game':
                app.menu_music.play()
            else:
                app.game_music.play()
        else:
            app.menu_music.stop()
            app.game_music.stop()
            
    def soundeffect(self, value):
        app.shot_enabled = value
        app.hit_enabled = value
        app.lose_enabled = value
        app.text_enabled = value
        app.noice_enabled = value
        app.coin_enabled = value
        
    def volume(self, value):
        app.menu_music.volume = value / 100
        app.game_music.volume = value / 100
        app.shot.volume = value / 100
        app.hit.volume = value / 100
        app.lose.volume = value / 100
        app.noice.volume = value / 100
        app.coin.volume = value / 100
        app.win.volume = value / 100
        for text_sound in app.text_sounds:
            text_sound.volume = value / 100

class GameScreen(MDScreen):
    app = MDApp.get_running_app()
    ship_x = NumericProperty(100)
    ship_y = NumericProperty(300)
    hp = NumericProperty(10)
    coins = NumericProperty(0)
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            Clock.schedule_interval(self.update, 1/60)
            self.eventkeys = {}
            self.cartridge = []
            self.cartridge_enemy = []
            self.asteroids = []
            self.enemys = []
            self.spawn_timer_asteroid = 0
            self.spawn_timer_enemy = 0
            self.paused = False
            
            self.stars = MoveStar(source='assets/image/stars.png', speed=20)
            self.planet = MovePlanet(source='assets/image/planet.png', speed=0.3)
            self.ids.bullets.add_widget(self.stars)
            self.ids.bullets.add_widget(self.planet)
            
    def pressKey(self, key):
        self.eventkeys[key] = True
        
    def releaseKey(self, key):
        self.eventkeys[key] = False 
            
    def update(self, dt):
        if self.manager.current != 'game':
            return
        
        if self.paused:
            return
        self.stars.move()
        self.planet.move()
        for key in self.eventkeys:
            if self.eventkeys[key] == True:
                if key == 'left':
                    self.moveLeft()
                if key == 'right':
                    self.moveRight()
                if key == 'up':
                    self.moveUP()
                if key == 'down':
                    self.moveDown()
                if key == 'shot':
                    self.player_shot()
                    self.eventkeys[key] = False
                    
        if self.eventkeys.get('left'):
            self.ids.space_ship.source = 'assets/image/ship/space-ship-stop_apng.png'
        elif self.eventkeys.get('right'):
            self.ids.space_ship.source = 'assets/image/ship/space-ship-run_apng.png'
        elif self.eventkeys.get('up'):
            self.ids.space_ship.source = 'assets/image/ship/space-ship-up_apng.png'
        elif self.eventkeys.get('down'):
            self.ids.space_ship.source = 'assets/image/ship/space-ship-down_apng.png'
        else:
            self.ids.space_ship.source = 'assets/image/ship/space-ship-idle_apng.png'
        #гравець
        for bullet in self.cartridge:
            bullet.x += 13
            for enemy in self.enemys[:]:
                if bullet.collide_widget(enemy):
                    enemy.enemy_hp -= 1
                    if app.hit_enabled:
                        app.hit.play()
                    self.ids.bullets.remove_widget(bullet)
                    self.cartridge.remove(bullet)
                    if enemy.enemy_hp <= 0:
                        self.ids.bullets.remove_widget(enemy)
                        self.enemys.remove(enemy)
                        self.coins += 10000
                    break
        #ворог
        for bullet in self.cartridge_enemy:
            bullet.x -= 13
            if bullet.collide_widget(self.ids.space_ship):
                self.hp -= 1
                if app.hit_enabled:
                    app.hit.play()
                self.ids.bullets.remove_widget(bullet)
                self.cartridge_enemy.remove(bullet)
            
        self.spawn_timer_asteroid += dt
        self.spawn_timer_enemy += dt

        if self.spawn_timer_asteroid >= 4:
            self.spawn_asteroid()
            self.spawn_timer_asteroid = 0
            
        if self.spawn_timer_enemy >= 5:
            self.spawn_enemy()
            self.spawn_timer_enemy = 0
            
        #астероїд
        for asteroid in self.asteroids[:]:
            asteroid.x -= 10
            if asteroid.collide_widget(self.ids.space_ship):
                self.hp -= 1
                if app.hit_enabled:
                    app.hit.play()
                self.ids.bullets.remove_widget(asteroid)
                self.asteroids.remove(asteroid)
            if asteroid.right < 0:
                self.ids.bullets.remove_widget(asteroid)
                self.asteroids.remove(asteroid)
                
        for enemy in self.enemys[:]:
            if enemy.right > Window.width*0.85:
                enemy.x -= 6
                enemy.source = 'assets/image/ship/space-ship-run-enemy_apng.png'
            else:
                enemy.source = 'assets/image/ship/space-ship-idle-enemy_apng.png'
            enemy.shot_timer += dt
            if enemy.shot_timer >= 2:
                self.enemy_shot(enemy)
                enemy.shot_timer = 0
                
        self.ids.health_hud.source = self.get_health_source(self.hp)
        
        if self.hp <= 0:
            self.game_over()
            
        if self.coins >= 1000000:
            self.game_win()
            
    def moveLeft(self):
        if self.ship_x > 0:
            self.ship_x -= 5

    def moveRight(self):
        if self.ship_x < Window.width - self.ids.space_ship.width:
            self.ship_x += 5

    def moveUP(self):
        if self.ship_y < Window.height - self.ids.space_ship.height:
            self.ship_y += 5

    def moveDown(self):
        if self.ship_y > 0:
            self.ship_y -= 5
            
    def spawn_asteroid(self):
        asteroid = Asteroid()  
        asteroid.pos = (Window.width, randint(0, int(Window.height - asteroid.height)))
        self.asteroids.append(asteroid)
        self.ids.bullets.add_widget(asteroid)
        
    def spawn_enemy(self):
        enemy = Enemy()
        enemy.pos = (Window.width, randint(0, int(Window.height - enemy.height)))
        self.enemys.append(enemy)
        self.ids.bullets.add_widget(enemy)
            
    def player_shot(self):
        if app.shot_enabled:
            app.shot.stop()
            app.shot.play()
        shot = Shot(pos=(self.ids.space_ship.right - 11, self.ids.space_ship.center_y - 20))
        self.cartridge.append(shot)
        self.ids.bullets.add_widget(shot)
        
    def enemy_shot(self, enemy):
        if app.shot_enabled:
            app.shot.stop()
            app.shot.play()
        shot_2 = Shot()
        shot_2.pos = (enemy.x - 20, enemy.center_y - 20)
        self.cartridge_enemy.append(shot_2)
        self.ids.bullets.add_widget(shot_2)
    
    def show_pause(self):
        self.paused = True
        self.ids.space_ship.anim_delay = -1
        for asteroid in self.asteroids:
            asteroid.anim_delay = -1
        for enemy in self.enemys:
            enemy.anim_delay = -1
        self.eventkeys.clear()
        
        self.ids.blocker_game.size_hint = (1, 1)
        self.ids.blocker_game.opacity = 1
        
        self.ids.pause_panel.size_hint = (0.25, 0.5)
        self.ids.pause_panel.opacity = 1
    
    def hide_pause(self):
        self.paused = False
        self.ids.space_ship.anim_delay = 1 / 8
        for asteroid in self.asteroids:
            asteroid.anim_delay = 1 / 20
        for enemy in self.enemys:
            enemy.anim_delay = 1/ 8
        
        self.ids.blocker_game.size_hint = (0, 0)
        self.ids.blocker_game.opacity = 0
                
        self.ids.pause_panel.size_hint = (0, 0)
        self.ids.pause_panel.opacity = 0
        
    def get_health_source(self, hp):
        hp = max(1, min(hp, 10))
        return f'assets/image/hp/health-hud-{hp}.png'
        
    def game_over(self):
        app.game_music.stop()
        game_over_screen = self.manager.get_screen('game_over')
        self.manager.transition = NoTransition()
        self.manager.current = 'game_over'
        
        game_over_screen.coins = self.coins
        game_over_screen.ids.health_hud.source = 'assets/image/hp/health-hud-1.png'
        
        if app.lose_enabled:
            app.lose.play()
        Clock.schedule_once(lambda dt: setattr(game_over_screen.ids.health_hud,'source', 'assets/image/hp/health-hud-0.png'),2)
        Clock.schedule_once(lambda dt: setattr(game_over_screen,'coins', -999999),2)
        Clock.schedule_once(lambda dt: setattr(game_over_screen.ids.health_hud,'opacity', 0),4)
        Clock.schedule_once(lambda dt: setattr(game_over_screen.ids.coin_hud,'opacity', 0),4)
        Clock.schedule_once(lambda dt: setattr(game_over_screen.ids.coin_label,'opacity', 0),4)
        Clock.schedule_once(lambda dt: game_over_screen.lose_text(), 7)
        
    def game_win(self):
        app.game_music.stop()
        game_win_screen = self.manager.get_screen('game_win')
        self.manager.transition = NoTransition()
        self.manager.current = 'game_win'
        
        game_win_screen.coins = 990000
        game_win_screen.ids.health_hud.source = self.ids.health_hud.source
        
        if app.coin_enabled:
            Clock.schedule_once(lambda dt: app.coin.play(), 2)
        Clock.schedule_once(lambda dt: setattr(game_win_screen,'coins', 1000000),3)
        Clock.schedule_once(lambda dt: setattr(game_win_screen.ids.health_hud,'opacity', 0),5)
        Clock.schedule_once(lambda dt: setattr(game_win_screen.ids.coin_hud,'opacity', 0),5)
        Clock.schedule_once(lambda dt: setattr(game_win_screen.ids.coin_label,'opacity', 0),5)
        Clock.schedule_once(lambda dt: game_win_screen.start_credits(), 10)
        Clock.schedule_once(lambda dt: app.go_to_menu(), 80)
        Clock.schedule_once(lambda dt: game_win_screen.reset_screen(), 83)
    
class GameOverScreen(MDScreen):
    coins = NumericProperty(0)
    def write(self, dt):
        if self.curr_lett >= len(self.all_text):
            Clock.schedule_once(lambda dt: setattr(self.ids.dialog_label,'opacity', 0),3)
            Clock.schedule_once(lambda dt: self.white(), 6)
            Clock.schedule_once(lambda dt: app.go_to_menu(), 20)
            Clock.schedule_once(lambda dt: self.reset_screen(), 23)
            return False
        self.ids.dialog_label.text += \
            self.all_text[self.curr_lett]
        self.curr_lett += 1
        if app.text_enabled:
            sound = choice(app.text_sounds)
            if sound:
                sound.stop()
                sound.play()
        
    def lose_text(self):
        self.all_text = 'You lose... But... You not done our deal.'
        self.curr_lett = 0
        self.ids.dialog_label.text = ''
        self.ids.dialog_label.opacity = 1
        Clock.schedule_interval(self.write, 0.1)
    
    def white(self):
        if app.noice_enabled:
            app.noice.play()
        Animation(opacity=1, duration=5).start(self.ids.end_white_screen)
        app.store.delete('save_game')
        
    def reset_screen(self):
        self.ids.health_hud.opacity = 1
        self.ids.coin_hud.opacity = 1
        self.ids.coin_label.opacity = 1
        self.ids.end_white_screen.opacity = 0
        self.ids.dialog_label.text = ''
        
class GameWinScreen(MDScreen):
    coins = NumericProperty(0)
    def start_credits(self):
        if app.win_enabled:
            app.win.play()
        self.ids.credits.opacity = 0
        self.ids.credits.text = '''
        KOTLETA IN THE SPACE
        
        THE GALAXY HAS BEEN SAVED
        
        THE MINCE HAS BEEN DEFEATED.
        
        THE ASTEROID ARE STILL HERE.
        BUT NOBODY CARES, XDDD.
        
        
        -------------------------------
        
        
        And you...
        
        NOW, YOU ARE THE NATIONAL HERO!
        
        All love you.
        You did what no one else would have done.
        Thanks to you, Kotletonia will continue to exist.
        
        
        -------------------------------
        
        
        CREATED BY: MARS
        
        ART & DESIGN: MARS
        
        PROGRAMMING: MARS
        
        IDEA: BOBKA
        
        
        -------------------------------
        
        
        SPECIAL THANKS
        
        Thanks to everyone
        who defended Kotletonia
        
        And thanks to the asteroids
        for not asking questions.
        
        
        -------------------------------
        
        THANKS YOU FOR PLAYING!)
        
        KOTLETONIA IS SAFE.
        
        FOR NOW...
        '''
        Clock.schedule_once(self.move_credits, 0)


    def move_credits(self, dt):
        self.ids.credits.y = -self.ids.credits.height
        self.ids.credits.opacity = 1
        Animation(y=Window.height, duration=65).start(self.ids.credits)
        app.store.delete('save_game')
        
    def reset_screen(self):
        self.ids.health_hud.opacity = 1
        self.ids.coin_hud.opacity = 1
        self.ids.coin_label.opacity = 1
        
        
class App(MDApp):
    brightness = NumericProperty(0.0)
    def build(self):
        self.music_enabled = True
        self.menu_music = SoundLoader.load('assets/sound/menu-music.mp3')
        self.menu_music.volume = 0.2
        self.menu_music.loop = True
        self.menu_music.play()
        self.game_music = SoundLoader.load('assets/sound/game-music.mp3')
        self.game_music.volume = 0.2
        self.game_music.loop = True
        self.shot = SoundLoader.load('assets/sound/laser-shot.mp3')
        self.shot_enabled = True
        self.shot.volume = 0.2
        self.hit = SoundLoader.load('assets/sound/get-hit.mp3')
        self.hit_enabled = True
        self.hit.volume = 0.2
        self.lose = SoundLoader.load('assets/sound/lose.mp3')
        self.lose_enabled = True
        self.lose.volume = 0.2
        self.noice = SoundLoader.load('assets/sound/white-noice.mp3')
        self.noice_enabled = True
        self.noice.volume = 0.2
        self.coin = SoundLoader.load('assets/sound/get_1mil.mp3')
        self.coin_enabled = True
        self.coin.volume = 0.2
        self.win = SoundLoader.load('assets/sound/win_music.mp3')
        self.win_enabled = True
        self.win.volume = 0.2
        self.text_sounds = [
            SoundLoader.load('assets/sound/sound_text/voice_1.mp3'),
            SoundLoader.load('assets/sound/sound_text/voice_2.mp3'),
            SoundLoader.load('assets/sound/sound_text/voice_3.mp3'),
            SoundLoader.load('assets/sound/sound_text/voice_4.mp3'),
            SoundLoader.load('assets/sound/sound_text/voice_5.mp3'),
            SoundLoader.load('assets/sound/sound_text/voice_6.mp3'),
            SoundLoader.load('assets/sound/sound_text/voice_7.mp3')
        ]
        self.text_enabled = True
        for text_sound in self.text_sounds:
            text_sound.volume = 0.2
        
        self.store = JsonStore("save.json")
        
        self.sm =  MDScreenManager()
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(GameScreen(name='game'))
        self.sm.add_widget(GameOverScreen(name='game_over'))
        self.sm.add_widget(GameWinScreen(name='game_win'))
        
        self.load_settings()
        
        return self.sm
    
    def new_game(self):
        game = self.sm.get_screen('game')
        game.hp = 10
        game.coins = 0
        game.ship_x = 100
        game.ship_y = 300
        for asteroid in game.asteroids[:]:
            game.ids.bullets.remove_widget(asteroid)
        game.asteroids.clear()
        for enemy in game.enemys[:]:
            game.ids.bullets.remove_widget(enemy)
        game.enemys.clear()
        self.save_game()
        game.hide_pause()
        self.sm.transition = FadeTransition(duration=1)
        self.play_game_music()
        self.sm.current = 'game'
        
    def save_game(self):
        game = self.sm.get_screen('game')
        asteroids_data = []
        enemys_data = []
        for asteroid in game.asteroids:
            asteroids_data.append({"x": asteroid.x, "y": asteroid.y})
        for enemy in game.enemys:
            enemys_data.append({"x": enemy.x, "y": enemy.y, 'hp': enemy.enemy_hp})
        self.store.put(
            'save_game',
            hp=game.hp,
            coins=game.coins,
            ship_x=game.ship_x,
            ship_y=game.ship_y,
            asteroids=asteroids_data,
            enemys=enemys_data
        )
        
    def load_game(self):
        if not self.store.exists('save_game'):
            return
        data = self.store.get('save_game')
        game = self.sm.get_screen('game')
        for enemy in game.enemys[:]:
            game.ids.bullets.remove_widget(enemy)
        game.enemys.clear()
        game.hp = data['hp']
        game.coins = data['coins']
        game.ship_x = data['ship_x']
        game.ship_y = data['ship_y']
        for asteroids_data in data['asteroids']:
            asteroid = Asteroid()
            asteroid.pos = (asteroids_data['x'], asteroids_data['y'])
            game.asteroids.append(asteroid)
            game.ids.bullets.add_widget(asteroid)
        for enemys_data in data['enemys']:
            enemy = Enemy()
            enemy.pos = (enemys_data['x'], enemys_data['y'])
            enemy.enemy_hp = enemys_data['hp']
            game.enemys.append(enemy)
            game.ids.bullets.add_widget(enemy)
        game.show_pause()
        self.sm.transition = FadeTransition(duration=1)
        self.play_game_music()
        self.sm.current = 'game'
        
    def load_settings(self):
        if not self.store.exists('save_settings'):
            return
        data = self.store.get('save_settings')
        menu = self.sm.get_screen('menu')
        menu.ids.music_checkbox.active = data['music']
        menu.ids.soundeffect_checkbox.active = data['sound']
        menu.ids.volume_slider.value = data['volume']
        menu.ids.vibration_checkbox.active = data['vibration']
        menu.ids.brightness_slider.value = data['brightness']
        self.sm.current = 'menu'
        
    def play_menu_music(self):
        if self.music_enabled:
            self.game_music.stop()
            self.menu_music.play()
        
    def play_game_music(self):
        if self.music_enabled:
            self.menu_music.stop()
            self.game_music.play()
        
    def go_to_menu(self, *args):
        self.sm.transition = FadeTransition(duration=1)
        self.play_menu_music()
        self.sm.current = 'menu'
    
    def quit(self):
        MDApp.get_running_app().stop()
    
if platform == 'android' or platform == 'ios':
    Window.fullscreen = 'auto'
else:
    Window.size = (1280, 520)

app = App()
app.run()