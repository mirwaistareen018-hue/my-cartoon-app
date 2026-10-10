
   from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

# زمین
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    color=color.green,
    texture='white_cube',
    texture_scale=(100, 100),
    collider='box'
)

# کھلاڑی کی گاڑی (کارٹون انداز)
player = Entity(
    model='cube',
    color=color.red,
    scale=(2, 1, 4),
    position=(0, 0.5, 0),
    collider='box'
)

# دشمن گاڑیاں
enemies = []
for i in range(3):
    enemy = Entity(
        model='cube',
        color=color.random_color(),
        scale=(2, 1, 4),
        position=(random.randint(-10, 10), 0.5, random.randint(20, 50)),
        collider='box'
    )
    enemies.append(enemy)

# کیمرہ پیروی
camera.position = (0, 8, -15)
camera.rotation_x = 20

speed = 10
score = 0

def update():
    global speed, score
    # کھلاڑی کی حرکت
    player.x += (held_keys['d'] - held_keys['a']) * time.dt * speed
    player.z += (held_keys['w'] - held_keys['s']) * time.dt * speed
    
    # کیمرہ پیروی
    camera.position = player.position + Vec3(0, 8, -15)
    
    # دشمن کی حرکت
    for enemy in enemies:
        enemy.z -= time.dt * 5
        if enemy.z < -20:
            enemy.z = random.randint(30, 60)
            enemy.x = random.randint(-10, 10)
            score += 1
            print(f"سکور: {score}")

app.run()
