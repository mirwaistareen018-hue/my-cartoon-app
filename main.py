
from ursina import *
from ursina.shaders import lit_with_shadows_shader
import random

app = Ursina()

# ---------- Lighting and Environment ----------
DirectionalLight(y=10, z=-10, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100, 100, 100, 0.3))
Sky(color=color.rgb(135, 206, 235))

# ---------- Ground (Racing Track) ----------
ground = Entity(
    model='plane',
    scale=(60, 1, 200),
    color=color.rgb(80, 80, 80),
    texture='white_cube',
    texture_scale=(6, 20),
    collider='box'
)

# ---------- Road Lines ----------
for i in range(-90, 90, 10):
    line = Entity(
        model='cube',
        color=color.yellow,
        scale=(0.3, 0.05, 3),
        position=(0, 0.55, i)
    )

# ---------- Grass on Sides ----------
left_grass = Entity(
    model='cube',
    color=color.green,
    scale=(30, 0.5, 200),
    position=(-45, 0, 0)
)
right_grass = Entity(
    model='cube',
    color=color.green,
    scale=(30, 0.5, 200),
    position=(45, 0, 0)
)

# ---------- Car Class ----------
class Car(Entity):
    def __init__(self, color_car, position=(0, 0, 0), is_player=False, **kwargs):
        super().__init__(position=position, **kwargs)
        self.is_player = is_player
        self.wheels = []
        
        # Car Body
        self.body = Entity(
            parent=self,
            model='cube',
            color=color_car,
            scale=(2, 0.8, 4),
            position=(0, 0.6, 0),
            shader=lit_with_shadows_shader
        )
        
        # Car Roof
        self.roof = Entity(
            parent=self,
            model='cube',
            color=color_car,
            scale=(1.6, 0.7, 2),
            position=(0, 1.3, -0.2),
            shader=lit_with_shadows_shader
        )
        
        # Wheels
        wheel_positions = [(-0.9, 0.3, 1.3), (0.9, 0.3, 1.3),
                          (-0.9, 0.3, -1.3), (0.9, 0.3, -1.3)]
        for wp in wheel_positions:
            wheel = Entity(
                parent=self,
                model='cylinder',
                color=color.black,
                scale=(0.6, 0.3, 0.6),
                position=wp,
                rotation=(0, 0, 90)
            )
            self.wheels.append(wheel)
        
        # Eyes (Cartoon Style)
        eye_l = Entity(parent=self, model='sphere', color=color.white,
                       scale=0.3, position=(-0.5, 1.4, 1.1))
        eye_r = Entity(parent=self, model='sphere', color=color.white,
                       scale=0.3, position=(0.5, 1.4, 1.1))
        Entity(parent=eye_l, model='sphere', color=color.black,
               scale=0.5, position=(0, 0, 0.6))
        Entity(parent=eye_r, model='sphere', color=color.black,
               scale=0.5, position=(0, 0, 0.6))

# ---------- Animal Class ----------
class Animal(Entity):
    def __init__(self, animal_color, position=(0, 0, 0), **kwargs):
        super().__init__(position=position, **kwargs)
        
        # Body
        Entity(parent=self, model='sphere', color=animal_color,
               scale=(2, 1.5, 3), position=(0, 1, 0),
               shader=lit_with_shadows_shader)
        
        # Head
        Entity(parent=self, model='sphere', color=animal_color,
               scale=1.2, position=(0, 2, 1.3),
               shader=lit_with_shadows_shader)
        
        # Ears
        Entity(parent=self, model='sphere', color=animal_color,
               scale=0.5, position=(-0.5, 2.7, 1.3))
        Entity(parent=self, model='sphere', color=animal_color,
               scale=0.5, position=(0.5, 2.7, 1.3))
        
        # Eyes
        eye_l = Entity(parent=self, model='sphere', color=color.white,
                       scale=0.35, position=(-0.4, 2.2, 1.9))
        eye_r = Entity(parent=self, model='sphere', color=color.white,
                       scale=0.35, position=(0.4, 2.2, 1.9))
        Entity(parent=eye_l, model='sphere', color=color.black,
               scale=0.5, position=(0, 0, 0.6))
        Entity(parent=eye_r, model='sphere', color=color.black,
               scale=0.5, position=(0, 0, 0.6))
        
        # Nose
        Entity(parent=self, model='sphere', color=color.black,
               scale=0.25, position=(0, 1.9, 2.2))
        
        # Legs
        for lp in [(-0.7, 0.5, 1), (0.7, 0.5, 1),
                   (-0.7, 0.5, -1), (0.7, 0.5, -1)]:
            Entity(parent=self, model='cylinder', color=animal_color,
                   scale=(0.4, 1, 0.4), position=lp)

# ---------- Player Car ----------
player_car = Car(color.red, position=(0, 0, -30), is_player=True)

# ---------- Enemy Cars ----------
enemy_cars = [
    Car(color.blue, position=(-5, 0, 20)),
    Car(color.yellow, position=(0, 0, 30)),
    Car(color.orange, position=(5, 0, 40)),
]

# ---------- Animals ----------
animals = [
    Animal(color.brown, position=(-8, 0, 10)),
    Animal(color.white, position=(8, 0, 15)),
    Animal(color.rgb(200, 150, 100), position=(-12, 0, 25)),
]

# ---------- UI Text ----------
score_text = Text(text='Score: 0', position=(-0.85, 0.45), scale=2, color=color.white)
speed_text = Text(text='Speed: 0', position=(-0.85, 0.40), scale=2, color=color.yellow)
win_text = Text(text='', position=(0, 0), scale=3, color=color.gold, origin=(0, 0))

# ---------- Camera ----------
camera.position = (0, 12, -45)
camera.rotation_x = 15

# ---------- Game State ----------
score = 0
game_won = False

# ---------- Update Function ----------
def update():
    global score, game_won
    
    if game_won:
        return
    
    # Player Movement
    move_x = (held_keys['d'] - held_keys['a']) * time.dt * 15
    move_z = (held_keys['w'] - held_keys['s']) * time.dt * 20
    
    player_car.x += move_x
    player_car.z += move_z
    
    # Boundaries
    player_car.x = max(-22, min(22, player_car.x))
    player_car.z = max(-95, min(95, player_car.z))
    
    # Car Tilting
    if move_x != 0:
        player_car.rotation_y = -move_x * 50
    
    # Wheel Rotation
    for wheel in player_car.wheels:
        wheel.rotation_x += move_z * 200
    
    # Enemy Cars Movement
    for enemy in enemy_cars:
        enemy.z -= time.dt * 12
        for wheel in enemy.wheels:
            wheel.rotation_x -= time.dt * 800
        
        # Collision Check
        if distance(player_car, enemy) < 3:
            win_text.text = 'Crash! Try Again (Press R)'
            win_text.color = color.red
            game_won = True
        
        # Respawn Enemy
        if enemy.z < -100:
            enemy.z = random.randint(60, 100)
            enemy.x = random.randint(-15, 15)
            score += 1
            score_text.text = f'Score: {score}'
    
    # Animals Movement
    for animal in animals:
        animal.z -= time.dt * 6
        if animal.z < -100:
            animal.z = random.randint(60, 100)
            animal.x = random.randint(-20, 20)
    
    # Win Condition
    if score >= 20:
        win_text.text = 'YOU WIN! Well Done!'
        win_text.color = color.gold
        game_won = True
    
    # Camera Follow
    camera.position = player_car.position + Vec3(0, 12, -45)
    camera.rotation_x = 15
    
    # Speed Display
    speed_text.text = f'Speed: {int(abs(move_z) * 50)}'

# ---------- Restart Function ----------
def input(key):
    global score, game_won
    if key == 'r' and game_won:
        score = 0
        game_won = False
        win_text.text = ''
        player_car.position = (0, 0, -30)
        for enemy in enemy_cars:
            enemy.position = (random.randint(-15, 15), 0, random.randint(20, 60))

app.run()
