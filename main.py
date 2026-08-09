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

Builder.load_file('menu.kv')
Builder.load_file('game.kv')

class Shot(Image):
    pass

class MenuScreen(MDScreen):
    
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


class GameScreen(MDScreen):
    ship_x = NumericProperty(100)
    ship_y = NumericProperty(300)
    hp = NumericProperty(10)
    coins = NumericProperty(0)
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            Clock.schedule_interval(self.update, 1/60)
            self.eventkeys = {}
            self.cartridge = []
            self.paused = False
            
    def on_enter(self, *args):
        if not self.paused:
            self.ids.space_ship.anim_delay = 1 / 8
            self.ids.bg_game.anim_delay = 1 / 24

            
    def pressKey(self, key):
        self.eventkeys[key] = True
        
    def releaseKey(self, key):
        self.eventkeys[key] = False 
            
    def update(self, dt):
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
                    self.shot()
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
            bullet.x += 10
            
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
            
    def shot(self):
        shot = Shot(pos=(self.ids.space_ship.right - 11, self.ids.space_ship.center_y - 20))
        self.cartridge.append(shot)
        self.ids.bullets.add_widget(shot)
    
    def show_pause(self):
        self.paused = True
        self.ids.space_ship.anim_delay = -1
        self.ids.bg_game.anim_delay = -1
        self.eventkeys.clear()
        
        self.ids.blocker_game.size_hint = (1, 1)
        self.ids.blocker_game.opacity = 1
        
        self.ids.pause_panel.size_hint = (0.25, 0.5)
        self.ids.pause_panel.opacity = 1
    
    def hide_pause(self):
        self.paused = False
        self.ids.space_ship.anim_delay = 1 / 8
        self.ids.bg_game.anim_delay = 1 / 24
        
        self.ids.blocker_game.size_hint = (0, 0)
        self.ids.blocker_game.opacity = 0
                
        self.ids.pause_panel.size_hint = (0, 0)
        self.ids.pause_panel.opacity = 0
        
    def go_to_menu(self, *args):
        self.manager.current = 'menu'
    

class App(MDApp):
    brightness = NumericProperty(0.0)
    def build(self):
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
        self.save_game()
        game.hide_pause()
        self.sm.current = 'game'
        
    def save_game(self):
        game = self.sm.get_screen('game')
        self.store.put(
            'save_game',
            hp=game.hp,
            coins=game.coins,
            ship_x=game.ship_x,
            ship_y=game.ship_y
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
        game.show_pause()
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
    
    def quit(self):
        MDApp.get_running_app().stop()
    
if platform == 'android' or platform == 'ios':
    Window.fullscreen = 'auto'
else:
    Window.size = (1280, 520)

app = App()
app.run()