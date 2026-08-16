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
from kivy.core.audio import SoundLoader
from random import randint, uniform

Builder.load_file('menu.kv')
Builder.load_file('game.kv')

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
    def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.source = 'assets/image/ship/space-ship-idle-enemy_apng.png'
            self.fit_mode = 'fill'
            self.anim_delay = 1 / 8
            self.size_hint = (0.15, 0.15)
            self.shot_timer = 0

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
        
    def volume(self, value):
        app.menu_music.volume = value / 100
        app.game_music.volume = value / 100
        app.shot.volume = value / 100

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
            
    def pressKey(self, key):
        self.eventkeys[key] = True
        
    def releaseKey(self, key):
        self.eventkeys[key] = False 
            
    def update(self, dt):
        if self.manager.current != 'game':
            return
        
        if self.paused:
            return
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
        
        for bullet in self.cartridge:
            bullet.x += 13
            
        for bullet in self.cartridge_enemy:
            bullet.x -= 13
            
        self.spawn_timer_asteroid += dt
        self.spawn_timer_enemy += dt

        if self.spawn_timer_asteroid >= 4:
            self.spawn_asteroid()
            self.spawn_timer_asteroid = 0
            
        if self.spawn_timer_enemy >= 5:
            self.spawn_enemy()
            self.spawn_timer_enemy = 0
            
        for asteroid in self.asteroids[:]:
            asteroid.x -= 10
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
        self.ids.bg_game.anim_delay = -1
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
        self.ids.bg_game.anim_delay = 1 / 24
        for asteroid in self.asteroids:
            asteroid.anim_delay = 1 / 20
        for enemy in self.enemys:
            enemy.anim_delay = 1/ 8
        
        self.ids.blocker_game.size_hint = (0, 0)
        self.ids.blocker_game.opacity = 0
                
        self.ids.pause_panel.size_hint = (0, 0)
        self.ids.pause_panel.opacity = 0
    

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
        
        self.store = JsonStore("save.json")
        
        self.sm =  MDScreenManager()
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(GameScreen(name='game'))
        
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
            enemys_data.append({"x": enemy.x, "y": enemy.y})
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