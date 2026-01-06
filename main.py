import pygame
import sys
import math
import random

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bounce Tales - Enhanced Edition")

# Colors
RED = (255, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_BLUE = (170, 220, 255)
ORANGE = (255, 165, 0)
PURPLE = (180, 70, 250)
DARK_GREEN = (30, 100, 60)
BROWN = (150, 100, 50)

# Game variables
clock = pygame.time.Clock()
FPS = 60
gravity = 0.3
score = 0
lives = 10000
level = 4
max_level = 5
game_state = "menu"  # menu, playing, game_over, win, paused

# Fonts
title_font = pygame.font.SysFont("Arial", 64, bold=True)
font_large = pygame.font.SysFont("Arial", 36)
font = pygame.font.SysFont("Arial", 24)
font_small = pygame.font.SysFont("Arial", 18)

# Sound effects (placeholder functions)
def play_jump_sound():
    pass

def play_coin_sound():
    pass

def play_hurt_sound():
    pass

def play_level_complete():
    pass

# Particle system
class Particle:
    def __init__(self, x, y, color, velocity=None, size=3, life=20):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        
        if velocity:
            self.vx, self.vy = velocity
        else:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 2)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1
        
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color[:3], alpha) if len(self.color) > 3 else self.color
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
    
    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()
    
    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)

# Game objects
class Ball:
    def __init__(self):
        self.radius = 20
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.vel_x = 0
        self.vel_y = 0
        self.jump_power = -14
        self.on_ground = False
        self.color = RED
        self.trail = []
        self.trail_length = 10
    
    def update(self, platforms, spikes, coins, goals, springs):
        global score, lives, level, game_state
        
        # Apply gravity
        self.vel_y += gravity
        
        # Apply friction
        self.vel_x *= 0.92
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Add to trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        
        # Boundary checking
        if self.x < self.radius:
            self.x = self.radius
            self.vel_x *= -0.5
        if self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.vel_x *= -0.5
        
        # Check if fell off the screen
        if self.y > HEIGHT + 100:
            lives -= 1
            play_hurt_sound()
            particle_system.add_particles(self.x, self.y, RED, 20)
            self.reset()
        
        # Check platform collisions
        self.on_ground = False
        for platform in platforms:
            if (self.y + self.radius >= platform.y and 
                self.y + self.radius <= platform.y + 10 and
                self.x + self.radius >= platform.x and 
                self.x - self.radius <= platform.x + platform.width and
                self.vel_y > 0):
                self.y = platform.y - self.radius
                self.vel_y = self.jump_power * 0.7  # Bounce
                self.on_ground = True
                particle_system.add_particles(self.x, self.y + self.radius, GREEN, 5)
        
        # Check spring collisions
        for spring in springs:
            if (self.x + self.radius > spring.x and 
                self.x - self.radius < spring.x + spring.width and
                self.y + self.radius > spring.y and 
                self.y - self.radius < spring.y + spring.height):
                self.vel_y = self.jump_power * 1.5  # Super bounce
                spring.animate()
                play_jump_sound()
                particle_system.add_particles(spring.x + spring.width/2, spring.y, YELLOW, 10)
        
        # Check spike collisions
        for spike in spikes:
            if (self.x + self.radius > spike.x and 
                self.x - self.radius < spike.x + spike.width and
                self.y + self.radius > spike.y and 
                self.y - self.radius < spike.y + spike.height):
                lives -= 1
                play_hurt_sound()
                particle_system.add_particles(self.x, self.y, RED, 20)
                self.reset()
                break
        
        # Check coin collisions
        for coin in coins[:]:
            if (math.sqrt((self.x - coin.x)**2 + (self.y - coin.y)**2) < self.radius + coin.radius):
                coins.remove(coin)
                score += 10
                play_coin_sound()
                particle_system.add_particles(coin.x, coin.y, YELLOW, 15)
        
        # Check goal collision
        for goal in goals:
            if (math.sqrt((self.x - goal.x)**2 + (self.y - goal.y)**2) < self.radius + goal.radius):
                level += 1
                play_level_complete()
                particle_system.add_particles(goal.x, goal.y, BLUE, 30)
                self.reset()
                if level > max_level:
                    game_state = "win"
                return True
        return False
    
    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            play_jump_sound()
            particle_system.add_particles(self.x, self.y + self.radius, WHITE, 8)
    
    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.vel_x = 0
        self.vel_y = 0
        self.trail = []

class Platform:
    def __init__(self, x, y, width, color=GREEN):
        self.x = x
        self.y = y
        self.width = width
        self.color = color
    
    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, 10))
        # Add platform details
        pygame.draw.rect(screen, DARK_GREEN, (self.x, self.y, self.width, 3))

class MovingPlatform(Platform):
    def __init__(self, x, y, width, min_x, max_x, speed):
        super().__init__(x, y, width, PURPLE)
        self.min_x = min_x
        self.max_x = max_x
        self.speed = speed
        self.direction = 1
    
    def update(self):
        self.x += self.speed * self.direction
        if self.x <= self.min_x or self.x + self.width >= self.max_x:
            self.direction *= -1

class Spring:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 12
        self.animation_frame = 0
    
    def draw(self):
        pygame.draw.rect(screen, ORANGE, (self.x, self.y - self.animation_frame, self.width, self.height))
        pygame.draw.rect(screen, (200, 100, 0), (self.x, self.y - self.animation_frame, self.width, 3))
    
    def animate(self):
        self.animation_frame = 5
        # Animation will be reset in the main game loop
    
    def update(self):
        if self.animation_frame > 0:
            self.animation_frame -= 0.2

class Spike:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 15
    
    def draw(self):
        pygame.draw.polygon(screen, GRAY, [
            (self.x, self.y + self.height),
            (self.x + self.width // 2, self.y),
            (self.x + self.width, self.y + self.height)
        ])
        # Add details
        pygame.draw.polygon(screen, (70, 70, 70), [
            (self.x + 5, self.y + self.height),
            (self.x + self.width // 2, self.y + 5),
            (self.x + self.width - 5, self.y + self.height)
        ])

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.color = YELLOW
        self.animation_time = 0
    
    def draw(self):
        self.animation_time += 0.1
        offset = math.sin(self.animation_time) * 3
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y + offset)), self.radius)
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y + offset)), self.radius - 3)
        pygame.draw.circle(screen, (255, 220, 100), (int(self.x), int(self.y + offset)), self.radius - 6)

class Goal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 25
        self.color = BLUE
        self.animation_time = 0
    
    def draw(self):
        self.animation_time += 0.05
        pulse = math.sin(self.animation_time) * 3 + self.radius
        pygame.draw.circle(screen, self.color, (self.x, self.y), pulse)
        pygame.draw.circle(screen, LIGHT_BLUE, (self.x, self.y), self.radius - 5)
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.radius - 10)

# Generate levels
def generate_level(level_num):
    platforms = []
    spikes = []
    coins = []
    goals = []
    springs = []
    
    # Base platform
    platforms.append(Platform(0, HEIGHT - 50, WIDTH, BROWN))
    
    if level_num == 1:
        platforms.append(Platform(100, 500, 200))
        platforms.append(Platform(50, 400, 100))
        platforms.append(Platform(250, 400, 100))
        platforms.append(Platform(150, 300, 100))
        
        spikes.append(Spike(200, 485))
        
        coins.append(Coin(150, 270))
        coins.append(Coin(250, 370))
        coins.append(Coin(80, 370))
        
        goals.append(Goal(200, 270))
        
        springs.append(Spring(350, 480))
    
    elif level_num == 2:
        platforms.append(Platform(50, 500, 100))
        platforms.append(Platform(200, 500, 100))
        platforms.append(Platform(50, 400, 100))
        platforms.append(Platform(200, 400, 100))
        platforms.append(Platform(125, 300, 150))
        platforms.append(Platform(50, 200, 100))
        platforms.append(Platform(200, 200, 100))
        platforms.append(Platform(125, 100, 150))
        
        platforms.append(MovingPlatform(300, 350, 100, 300, 600, 2))
        
        spikes.append(Spike(150, 480))
        spikes.append(Spike(150, 380))
        
        coins.append(Coin(80, 180))
        coins.append(Coin(250, 180))
        coins.append(Coin(180, 480))
        coins.append(Coin(350, 330))
        
        goals.append(Goal(180, 80))
        
        springs.append(Spring(400, 480))
    
    elif level_num == 3:
        platforms.append(Platform(100, 500, 100))
        platforms.append(Platform(300, 500, 100))
        platforms.append(Platform(500, 500, 100))
        
        platforms.append(MovingPlatform(100, 400, 100, 100, 400, 3))
        platforms.append(MovingPlatform(500, 400, 100, 400, 700, 3))
        
        platforms.append(Platform(100, 300, 100))
        platforms.append(Platform(300, 300, 100))
        platforms.append(Platform(500, 300, 100))
        
        platforms.append(MovingPlatform(100, 200, 100, 100, 400, 3))
        platforms.append(MovingPlatform(500, 200, 100, 400, 700, 3))
        
        platforms.append(Platform(300, 100, 100))
        
        spikes.append(Spike(300, 480))
        spikes.append(Spike(200, 380))
        spikes.append(Spike(400, 380))
        spikes.append(Spike(300, 280))
        
        coins.append(Coin(150, 480))
        coins.append(Coin(350, 480))
        coins.append(Coin(250, 380))
        coins.append(Coin(450, 380))
        coins.append(Coin(150, 280))
        coins.append(Coin(350, 280))
        coins.append(Coin(300, 80))
        
        goals.append(Goal(300, 80))
        
    
    
    elif level_num == 4:
        # Add more challenging levels
        platforms.append(MovingPlatform(100, 500, 100, 100, 500, 2))
        platforms.append(MovingPlatform(600, 450, 100, 400, 600, 2))
        platforms.append(MovingPlatform(200, 400, 100, 200, 600, 3))
        platforms.append(MovingPlatform(500, 350, 100, 100, 500, 3))
        platforms.append(MovingPlatform(300, 300, 100, 100, 500, 4))
        platforms.append(MovingPlatform(100, 250, 100, 100, 400, 2))
        platforms.append(MovingPlatform(600, 200, 100, 300, 600, 2))
        platforms.append(Platform(350, 150, 100))
        
        
        
        for i in range(8):
            coins.append(Coin(100 + i*80, 450 - i*40))
        
        goals.append(Goal(400, 130))
        
       
    
    elif level_num == 5:
        # Final challenging level
        platforms.append(MovingPlatform(100, 550, 80, 100, 700, 3))
        platforms.append(MovingPlatform(600, 500, 80, 100, 600, 3))
        platforms.append(MovingPlatform(200, 450, 80, 200, 600, 4))
        platforms.append(MovingPlatform(500, 400, 80, 100, 500, 4))
        platforms.append(MovingPlatform(300, 350, 80, 100, 500, 5))
        platforms.append(MovingPlatform(100, 300, 80, 100, 400, 3))
        platforms.append(MovingPlatform(600, 250, 80, 300, 600, 3))
        platforms.append(MovingPlatform(400, 200, 80, 200, 600, 4))
        platforms.append(Platform(350, 150, 80))
        
        
        
        for i in range(10):
            x = random.randint(50, WIDTH-50)
            y = random.randint(100, 500)
            coins.append(Coin(x, y))
        
        goals.append(Goal(390, 130))
        
        springs.append(Spring(200, 530))
        springs.append(Spring(500, 380))
        springs.append(Spring(300, 230))
    
    return platforms, spikes, coins, goals, springs

# Draw functions
def draw_game():
    # Draw background
    screen.fill(LIGHT_BLUE)
    
    # Draw background details
    for i in range(10):
        cloud_x = (i * 200 + pygame.time.get_ticks() // 50) % (WIDTH + 200) - 100
        cloud_y = 50 + (i % 3) * 40
        pygame.draw.circle(screen, WHITE, (int(cloud_x), cloud_y), 20)
        pygame.draw.circle(screen, WHITE, (int(cloud_x + 15), cloud_y - 10), 15)
        pygame.draw.circle(screen, WHITE, (int(cloud_x + 30), cloud_y), 20)
    
    # Draw platforms
    for platform in platforms:
        platform.draw()
    
    # Draw spikes
    for spike in spikes:
        spike.draw()
    
    # Draw springs
    for spring in springs:
        spring.draw()
    
    # Draw coins
    for coin in coins:
        coin.draw()
    
    # Draw goals
    for goal in goals:
        goal.draw()
    
    # Draw ball trail
    for i, (trail_x, trail_y) in enumerate(ball.trail):
        alpha = i / len(ball.trail) * 200
        pygame.draw.circle(screen, (255, 100, 100, alpha), (int(trail_x), int(trail_y)), ball.radius - i/2)
    
    # Draw ball
    pygame.draw.circle(screen, ball.color, (int(ball.x), int(ball.y)), ball.radius)
    pygame.draw.circle(screen, (255, 150, 150), (int(ball.x), int(ball.y)), ball.radius - 5)
    
    # Draw eyes
    pygame.draw.circle(screen, WHITE, (int(ball.x) - 7, int(ball.y) - 5), 6)
    pygame.draw.circle(screen, WHITE, (int(ball.x) + 7, int(ball.y) - 5), 6)
    pygame.draw.circle(screen, BLACK, (int(ball.x) - 7, int(ball.y) - 5), 3)
    pygame.draw.circle(screen, BLACK, (int(ball.x) + 7, int(ball.y) - 5), 3)
    
    # Draw UI
    score_text = font_large.render(f"Score: {score}", True, BLACK)
    lives_text = font_large.render(f"Lives: {lives}", True, BLACK)
    level_text = font_large.render(f"Level: {level}/{max_level}", True, BLACK)
    
    screen.blit(score_text, (20, 20))
    screen.blit(lives_text, (WIDTH - 150, 20))
    screen.blit(level_text, (WIDTH // 2 - 70, 20))
    
    # Draw particles
    particle_system.draw(screen)
    
    pygame.display.flip()

def draw_menu():
    screen.fill(LIGHT_BLUE)
    
    # Draw title
    title = title_font.render("Bounce Tales", True, RED)
    subtitle = font_large.render("Enhanced Edition", True, BLUE)
    
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 180))
    
    # Draw menu options
    if pygame.time.get_ticks() % 1000 < 800:  # Blinking effect
        start_text = font_large.render("Press SPACE to Start", True, GREEN)
        screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, 300))
    
    controls_text = font.render("Controls: Arrow Keys to Move, SPACE to Jump", True, BLACK)
    screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, 400))
    
    quit_text = font.render("Press Q to Quit", True, BLACK)
    screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, 450))
    
    # Draw a bouncing ball
    bounce_y = 500 + math.sin(pygame.time.get_ticks() / 200) * 20
    pygame.draw.circle(screen, RED, (WIDTH // 2, int(bounce_y)), 30)
    
    pygame.display.flip()

def draw_game_over():
    screen.fill(LIGHT_BLUE)
    
    game_over_text = title_font.render("GAME OVER", True, RED)
    score_text = font_large.render(f"Final Score: {score}", True, BLACK)
    restart_text = font.render("Press R to Restart", True, BLACK)
    menu_text = font.render("Press M for Menu", True, BLACK)
    
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 150))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 320))
    screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, 370))
    
    pygame.display.flip()

def draw_win_screen():
    screen.fill(LIGHT_BLUE)
    
    win_text = title_font.render("YOU WIN!", True, GREEN)
    score_text = font_large.render(f"Final Score: {score}", True, BLACK)
    restart_text = font.render("Press R to Play Again", True, BLACK)
    menu_text = font.render("Press M for Menu", True, BLACK)
    
    screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, 150))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 320))
    screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, 370))
    
    # Draw celebration particles
    particle_system.draw(screen)
    
    pygame.display.flip()

def draw_pause_screen():
    # Draw semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    pause_text = title_font.render("PAUSED", True, WHITE)
    continue_text = font_large.render("Press P to Continue", True, WHITE)
    menu_text = font_large.render("Press M for Menu", True, WHITE)
    
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 200))
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, 300))
    screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, 350))
    
    pygame.display.flip()

# Initialize game objects
ball = Ball()
particle_system = ParticleSystem()
platforms, spikes, coins, goals, springs = generate_level(level)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            
            if game_state == "menu":
                if event.key == pygame.K_SPACE:
                    game_state = "playing"
            
            elif game_state == "playing":
                if event.key == pygame.K_SPACE:
                    ball.jump()
                if event.key == pygame.K_p:
                    game_state = "paused"
            
            elif game_state == "paused":
                if event.key == pygame.K_p:
                    game_state = "playing"
                if event.key == pygame.K_m:
                    game_state = "menu"
                    # Reset game
                    score = 0
                    lives = 3
                    level = 1
                    ball = Ball()
                    platforms, spikes, coins, goals, springs = generate_level(level)
            
            elif game_state == "game_over" or game_state == "win":
                if event.key == pygame.K_r:
                    # Reset game
                    score = 0
                    lives = 3
                    level = 1
                    ball = Ball()
                    platforms, spikes, coins, goals, springs = generate_level(level)
                    game_state = "playing"
                if event.key == pygame.K_m:
                    game_state = "menu"
                    # Reset game
                    score = 0
                    lives = 3
                    level = 1
                    ball = Ball()
                    platforms, spikes, coins, goals, springs = generate_level(level)
    
    # Get keyboard state for continuous movement
    keys = pygame.key.get_pressed()
    if game_state == "playing":
        if keys[pygame.K_LEFT]:
            ball.vel_x = -7
        elif keys[pygame.K_RIGHT]:
            ball.vel_x = 7
    
    # Update game state
    if game_state == "playing":
        # Update moving platforms
        for platform in platforms:
            if isinstance(platform, MovingPlatform):
                platform.update()
        
        # Update springs
        for spring in springs:
            spring.update()
        
        # Update particles
        particle_system.update()
        
        # Update ball
        level_complete = ball.update(platforms, spikes, coins, goals, springs)
        
        if level_complete:
            platforms, spikes, coins, goals, springs = generate_level(level)
        
        if lives <= 0:
            game_state = "game_over"
            particle_system.add_particles(WIDTH//2, HEIGHT//2, RED, 50)
        
        if level > max_level:
            game_state = "win"
            particle_system.add_particles(WIDTH//2, HEIGHT//2, (255, 255, 0), 50)
    
    # Draw the appropriate screen
    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        draw_game()
    elif game_state == "game_over":
        draw_game_over()
    elif game_state == "win":
        draw_win_screen()
    elif game_state == "paused":
        draw_game()
        draw_pause_screen()
    
    clock.tick(FPS)

pygame.quit()
sys.exit()