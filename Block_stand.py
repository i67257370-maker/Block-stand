from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
import random
import json
import os

NEON_PALETTE = [
    (0, 0.8, 1, 1), (1, 0, 0.5, 1), (0.4, 1, 0.2, 1), (1, 0.7, 0, 1), (0.6, 0.2, 1, 1)
]

SMALL_SHAPES = [[(0,0)], [(0,0), (0,1)], [(0,0), (1,0)], [(0,0), (0,1), (1,0)], [(0,1), (1,1), (1,0)]]
BIG_SHAPES = [[(0,0), (0,1), (0,2)], [(0,0), (1,0), (2,0)], [(0,0), (0,1), (1,0), (1,1)], 
              [(0,1), (1,0), (1,1), (1,2), (2,1)], [(0,0), (0,1), (0,2), (0,3), (0,4)]]

class FloatingText(Label):
    def __init__(self, text, pos, color=(1, 1, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = '40sp'
        self.bold = True
        self.color = color
        self.pos = pos
        # Анимация взлета и исчезновения
        anim = Animation(y=self.y + 150, opacity=0, d=1, t='out_quad')
        anim.bind(on_complete=lambda *args: self.parent.remove_widget(self) if self.parent else None)
        anim.start(self)

class Particle(Widget):
    def __init__(self, pos, color, **kwargs):
        super().__init__(**kwargs)
        self.size = (10, 10)
        self.pos = pos
        with self.canvas:
            Color(*color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        dest_x = self.x + random.uniform(-100, 100)
        dest_y = self.y + random.uniform(-150, 150)
        anim = Animation(pos=(dest_x, dest_y), opacity=0, duration=0.6)
        anim.bind(on_complete=lambda *args: self.parent.remove_widget(self) if self.parent else None)
        anim.start(self)

class DraggableShape(Widget):
    def __init__(self, shape_template, cell_size, pos, **kwargs):
        super().__init__(**kwargs)
        self.shape_template = shape_template
        self.cell_size = cell_size
        self.pos = pos
        self.start_pos = pos
        self.block_color = random.choice(NEON_PALETTE)
        self.current_scale = 0.7 if len(shape_template) <= 3 else 0.5
        self.bind(pos=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            d_size = self.cell_size * self.current_scale
            for dr, dc in self.shape_template:
                Color(*self.block_color)
                RoundedRectangle(pos=(self.x + dc*d_size, self.y + dr*d_size), 
                                 size=(d_size-2, d_size-2), radius=[5,])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.current_scale = 1.0
            self.redraw()
            touch.grab(self)
            return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.pos = (touch.x - self.cell_size, touch.y + self.cell_size)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            game = self.parent
            if game and hasattr(game, 'try_place_shape') and game.try_place_shape(self):
                game.remove_widget(self)
                game.check_spawn()
            else:
                self.current_scale = 0.7 if len(self.shape_template) <= 3 else 0.5
                anim = Animation(pos=self.start_pos, duration=0.1)
                anim.bind(on_complete=lambda *a: self.redraw())
                anim.start(self)
            return True
        return False

class BlockBlastGame(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cell_size = Window.width / 8.8
        self.origin_x = (Window.width - self.cell_size * 8) / 2
        self.origin_y = Window.height * 0.22 
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.score = 0
        self.high_score = self.load_score()
        
        self.board_layer = Widget()
        self.add_widget(self.board_layer)
        
        self.hs_label = Label(text=f"BEST: {self.high_score}", font_size='18sp',
                             size_hint=(None, None), size=(Window.width, 40),
                             x=0, top=Window.height - 35, color=(0.4, 0.6, 1, 1))
        
        self.score_label = Label(text="0", font_size='48sp', bold=True,
                                size_hint=(None, None), size=(Window.width, 60),
                                x=0, top=Window.height - 75)
        
        self.add_widget(self.hs_label)
        self.add_widget(self.score_label)
        
        self.render_board()
        self.spawn_shapes()

    def load_score(self):
        if os.path.exists('highscore.json'):
            try:
                with open('highscore.json', 'r') as f: return json.load(f).get('score', 0)
            except: return 0
        return 0

    def try_place_shape(self, shape):
        c, r = round((shape.x - self.origin_x) / self.cell_size), round((shape.y - self.origin_y) / self.cell_size)
        cells = []
        for dr, dc in shape.shape_template:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] is None: cells.append((nr, nc))
            else: return False
        
        for nr, nc in cells: self.board[nr][nc] = shape.block_color
        self.update_score(len(cells) * 10)
        self.check_lines()
        self.render_board()
        return True

    def update_score(self, pts, combo=1):
        self.score += (pts * combo)
        self.score_label.text = str(self.score)
        if self.score > self.high_score:
            self.high_score = self.score
            self.hs_label.text = f"BEST: {self.high_score}"
            with open('highscore.json', 'w') as f: json.dump({'score': self.high_score}, f)

    def check_lines(self):
        rows = [r for r in range(8) if all(self.board[r])]
        cols = [c for c in range(8) if all(self.board[r][c] for r in range(8))]
        
        total_lines = len(rows) + len(cols)
        if total_lines > 0:
            # Тряска экрана
            if total_lines > 1:
                anim = Animation(x=5, duration=0.05) + Animation(x=-5, duration=0.05) + Animation(x=0, duration=0.05)
                anim.start(self)
                # Надпись COMBO
                self.add_widget(FloatingText(f"COMBO x{total_lines}!", (0, Window.height * 0.4), (1, 0.8, 0, 1)))

            for r in rows:
                for c in range(8):
                    self.create_particles(r, c, self.board[r][c])
                    self.board[r][c] = None
            for c in cols:
                for r in range(8):
                    if self.board[r][c]:
                        self.create_particles(r, c, self.board[r][c])
                        self.board[r][c] = None
            
            # Проверка на PERFECT (пустое поле)
            is_empty = all(self.board[r][c] is None for r in range(8) for c in range(8))
            if is_empty:
                self.update_score(5000)
                self.add_widget(FloatingText("PERFECT!!!", (0, Window.height * 0.5), (0.4, 1, 0.2, 1)))

            self.update_score(total_lines * 100, combo=total_lines)

    def create_particles(self, r, c, color):
        if not color: color = (1, 1, 1, 1)
        pos = (self.origin_x + c * self.cell_size + self.cell_size/2, 
               self.origin_y + r * self.cell_size + self.cell_size/2)
        for _ in range(4): self.add_widget(Particle(pos, color))

    def render_board(self):
        self.board_layer.canvas.clear()
        with self.board_layer.canvas:
            Color(0.1, 0.1, 0.2, 1)
            RoundedRectangle(pos=(self.origin_x - 5, self.origin_y - 5), 
                             size=(self.cell_size * 8 + 10, self.cell_size * 8 + 10), radius=[10,])
            for r in range(8):
                for c in range(8):
                    pos = (self.origin_x + c * self.cell_size, self.origin_y + r * self.cell_size)
                    if self.board[r][c]:
                        Color(*self.board[r][c]); RoundedRectangle(pos=pos, size=(self.cell_size-2, self.cell_size-2), radius=[4,])
                    else:
                        Color(1, 1, 1, 0.05); RoundedRectangle(pos=pos, size=(self.cell_size-2, self.cell_size-2), radius=[2,])

    def spawn_shapes(self):
        spacing = Window.width / 3
        for i in range(3):
            pool = SMALL_SHAPES if random.random() > 0.5 else BIG_SHAPES
            template = random.choice(pool)
            p = (spacing * i + (spacing - self.cell_size*1.2)/2, Window.height * 0.05)
            self.add_widget(DraggableShape(template, self.cell_size, p))
        Clock.schedule_once(lambda dt: self.check_game_over(), 0.2)

    def check_game_over(self):
        shapes = [w for w in self.children if isinstance(w, DraggableShape)]
        if not shapes: return
        can_move = False
        for s in shapes:
            for r in range(8):
                for c in range(8):
                    fits = True
                    for dr, dc in s.shape_template:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] is None):
                            fits = False; break
                    if fits: can_move = True; break
                if can_move: break
            if can_move: break
        if not can_move: self.show_game_over()

    def show_game_over(self):
        self.go_label = Label(text=f"GAME OVER\nSCORE: {self.score}", font_size='30sp', bold=True,
                             halign='center', pos_hint={'center_x': 0.5, 'center_y': 0.6})
        self.restart_btn = Button(text="RESTART", size_hint=(0.4, 0.1),
                                 pos_hint={'center_x': 0.5, 'center_y': 0.45},
                                 background_color=(1, 0, 0.4, 1))
        self.restart_btn.bind(on_release=lambda x: self.restart())
        self.add_widget(self.go_label)
        self.add_widget(self.restart_btn)

    def restart(self):
        self.clear_widgets()
        self.__init__()

    def check_spawn(self):
        if not any(isinstance(w, DraggableShape) for w in self.children):
            self.spawn_shapes()
        else:
            self.check_game_over()

class MainApp(App):
    def build(self): 
        Window.clearcolor = (0.01, 0.01, 0.05, 1)
        return BlockBlastGame()

if __name__ == '__main__':
    MainApp().run()
