import pygame
import cv2
import numpy as np
import random
from sys import exit
import os

# Initialization
pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FlappyArms")

# Screen capture init
cap = cv2.VideoCapture(0)
cascade_path = "haarcascade_frontalface_default.xml"
if not os.path.isfile(cascade_path):
    print(f"Error: Cascade classifier not found at {cascade_path}")
    exit()
face_cascade = cv2.CascadeClassifier(cascade_path)
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# Font
font = pygame.font.Font("assets/ataurus.ttf", 72)
score_font = pygame.font.Font("assets/ataurus.ttf", 36)

# Loading images
base_img = pygame.image.load("assets/base.png")
base_img = pygame.transform.scale(base_img, (1600, 100)).convert()

bird_sprites = [
    pygame.image.load("assets/bird-upflap.png").convert(),
    pygame.image.load("assets/bird-midflap.png").convert(),
    pygame.image.load("assets/bird-downflap.png").convert()
]

bottom_pipe_img = pygame.image.load("assets/pipe-green.png").convert()
top_pipe_img = pygame.image.load("assets/pipe-green.png")
top_pipe_img = pygame.transform.rotate(top_pipe_img, 180).convert()

game_over_img = pygame.image.load("assets/game_over.png")

start_img = pygame.image.load("assets/start.png")

icon_img = pygame.image.load("assets/icon.png")
pygame.display.set_icon(icon_img)


class Base(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.img = base_img
        self.x_pos = 0
        self.x_displacement = -10

    def update(self):
        if not pause_movement:
            self.x_pos += self.x_displacement
        if self.x_pos <= -WIDTH:
            self.x_pos = 0
        SCREEN.blit(self.img, (self.x_pos, 500))


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.sprites = bird_sprites
        self.rects = [sprite.get_rect() for sprite in self.sprites]
        self.current_index = 1
        self.rect = self.rects[self.current_index]
        self.frame_count = 0
        self.prev_center_y_pos = None
        self.alive = True
        self.fall_speed = 0
        self.rotation_angle = 0

    def update(self, face_pos):
        if self.alive:
            self.frame_count += 1
            if self.frame_count > 5:
                self.frame_count = 0
                self.current_index = (self.current_index + 1) % 3
                self.bird_rect = self.rects[self.current_index]

            if face_pos is not None and self.alive:
                (x, y, w, h) = face_pos
                # print(h)
                center_y_pos = y + 110
                if self.prev_center_y_pos is not None:
                    delta = center_y_pos - self.prev_center_y_pos
                    if abs(delta) > 15:
                        center_y_pos = self.prev_center_y_pos + \
                            (15 if delta > 0 else -15)

                self.prev_center_y_pos = center_y_pos
                self.rect.center = (100, center_y_pos)

                # Warnings for face distance
                if h > 110:
                    warning_surface = font.render(
                        "Move farther", True, (0, 0, 0))
                    warning_rect = warning_surface.get_rect(
                        center=(WIDTH // 2, HEIGHT // 2))
                    SCREEN.blit(warning_surface, warning_rect)
                elif h < 80:
                    warning_surface = font.render(
                        "Move closer", True, (0, 0, 0))
                    warning_rect = warning_surface.get_rect(
                        center=(WIDTH // 2, HEIGHT // 2))
                    SCREEN.blit(warning_surface, warning_rect)
                SCREEN.blit(self.sprites[self.current_index], self.rect)

            elif self.prev_center_y_pos is not None:
                self.rect.center = (100, self.prev_center_y_pos)
                SCREEN.blit(self.sprites[self.current_index], self.rect)
            else:
                self.rect.center = (
                    100, HEIGHT // 2)
                SCREEN.blit(self.sprites[self.current_index], self.rect)
        else:
            self.fall_speed += 5  # Grav effect
            self.rect.y += self.fall_speed
            if self.rect.bottom >= 500:
                self.rect.bottom = 500
            if self.rotation_angle >= -90:
                self.rotation_angle += -8
            rotated_bird = pygame.transform.rotate(
                self.sprites[self.current_index], self.rotation_angle)
            SCREEN.blit(rotated_bird, self.rect)


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, is_bottom):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.is_bottom = is_bottom
        self.passed = False

    def update(self):
        if not pause_movement:
            self.rect.x += pipe_displacement
        if self.rect.x <= -60:
            self.kill()


# Game variables
FPS = 60
clock = pygame.time.Clock()
pipe_displacement = -10
score = 0
pause_movement = True
game_stopped = True


def quit_game():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            pygame.quit()
            exit()


def capture_frame():
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame")
        return None

    # Convert the frame from BGR (OpenCV) to RGB (Pygame)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame


def draw_camera(frame):
    frame = np.rot90(frame)
    frame_surface = pygame.surfarray.make_surface(frame)
    SCREEN.blit(pygame.transform.scale(frame_surface, (WIDTH, HEIGHT)), (0, 0))


def load_high_score():
    try:
        with open("highscore.txt", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))


high_score = load_high_score()


def menu():
    global pause_movement
    while game_stopped:
        quit_game()

        frame = capture_frame()
        draw_camera(frame)

        SCREEN.blit(base_img, (0, 500))
        SCREEN.blit(bird_sprites[1], (100, HEIGHT // 2))
        SCREEN.blit(start_img, (WIDTH // 2 - start_img.get_width() // 2,
                                HEIGHT // 2 - start_img.get_height() // 2))

        # Display high score on the menu screen
        high_score_text = score_font.render(
            f"High Score: {high_score}", True, (0, 0, 0))
        SCREEN.blit(high_score_text, (WIDTH // 2 -
                    high_score_text.get_width() // 2, HEIGHT // 2 + 100))

        # User input
        user_input = pygame.key.get_pressed()
        if user_input[pygame.K_SPACE]:
            pause_movement = False
            main()

        pygame.display.update()


# Game loop
def main():
    global score, pause_movement, high_score

    bird = Bird()
    base = Base()
    pipes = pygame.sprite.Group()

    pipe_timer = 0

    running = True
    while running:
        quit_game()

        frame = capture_frame()
        if frame is None:  # Handle case where frame is not captured
            continue

        draw_camera(frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.05, 5)

        # pipe_positions = [
        #    f"(x = {pipe.rect.x}, y = {pipe.rect.y})" for pipe in pipes]
        # print(" | ".join(pipe_positions))

        # Draw pipes
        pipes.draw(SCREEN)
        pipes.update()

        # Draw background
        base.update()

        # Bird animation
        if len(faces) > 0:
            bird.update(faces[0])
        else:
            bird.update(None)

        # Spawn pipes
        if pipe_timer <= 0 and bird.alive:
            x_pos = 1500
            y_top = random.randint(-240, 0)
            y_bottom = y_top + \
                random.randint(100, 150) + bottom_pipe_img.get_height()
            pipes.add(Pipe(x_pos, y_top, top_pipe_img, is_bottom=False))
            pipes.add(Pipe(x_pos, y_bottom, bottom_pipe_img, is_bottom=True))
            pipe_timer = random.randint(30, 40)
        pipe_timer -= 1

        # Check if bird passed pipe and collision
        for pipe in pipes:
            if pipe.is_bottom and not pipe.passed and pipe.rect.right < bird.rect.left:
                pipe.passed = True
                score += 1
            elif bird.rect.colliderect(pipe.rect) or bird.rect.bottom >= 500:
                pause_movement = True
                bird.alive = False
                game_over_rect = game_over_img.get_rect(
                    center=(WIDTH // 2, HEIGHT // 2))
                SCREEN.blit(game_over_img, game_over_rect)

                # Check if current score is a new high score
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

        # Show score
        score_text = score_font.render(
            str(score), True, pygame.Color(0, 0, 0))
        SCREEN.blit(score_text, (20, 20))

        # User input
        user_input = pygame.key.get_pressed()
        if user_input[pygame.K_r] and not bird.alive:
            score = 0
            break

        clock.tick(FPS)
        pygame.display.update()


menu()
