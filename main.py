import pygame
import random
import time

pygame.init()

# === Config ===
BLOCK_SIZE = 30
COLS = 10
ROWS = 20
WIDTH = BLOCK_SIZE * COLS
HEIGHT = BLOCK_SIZE * ROWS
GAP = 60
EXTRA_HEIGHT = 80
FPS = 5
GRAVITY_DELAY = 1000  # milliseconds

window_size = (WIDTH * 2 + GAP, HEIGHT + EXTRA_HEIGHT)
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.display.set_caption("2 Player Tetris")
font = pygame.font.SysFont("Arial", 28)

shapes = {
    'O': [[1, 1], [1, 1]],
    'I': [[1, 1, 1, 1]],
    'S': [[0, 1, 1], [1, 1, 0]],
    'Z': [[1, 1, 0], [0, 1, 1]],
    'L': [[1, 0, 0], [1, 1, 1]],
    'J': [[0, 0, 1], [1, 1, 1]],
    'T': [[0, 1, 0], [1, 1, 1]],
}

colors = {
    'O': (255, 255, 0),
    'I': (0, 255, 255),
    'S': (0, 255, 0),
    'Z': (255, 0, 0),
    'L': (255, 165, 0),
    'J': (0, 0, 255),
    'T': (160, 32, 240),
    'X': (100, 100, 100),
}

class BagQueue:
    def __init__(self):
        self.queue = []

    def refill(self):
        bag = list(shapes.keys())
        random.shuffle(bag)
        self.queue.extend(bag)

    def next(self):
        if not self.queue:
            self.refill()
        return self.queue.pop(0)

bag_queue = BagQueue()

def random_piece():
    type_ = bag_queue.next()
    return {'type': type_, 'shape': shapes[type_], 'x': 3, 'y': 0}

def create_grid():
    return [[''] * COLS for _ in range(ROWS)]

def draw_grid(grid, offset_x, offset_y=None, scale=1.0):
    if offset_y is None:
        offset_x += (screen.get_width() - (WIDTH * 2 + GAP)) // 2
        offset_y = (screen.get_height() - (HEIGHT + EXTRA_HEIGHT)) // 2
    for y in range(ROWS):
        for x in range(COLS):
            color = colors.get(grid[y][x], (30, 30, 30))
            rect = pygame.Rect(
                offset_x + x * BLOCK_SIZE * scale,
                offset_y + y * BLOCK_SIZE * scale,
                BLOCK_SIZE * scale,
                BLOCK_SIZE * scale
            )
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

def draw_piece(piece, offset_x, offset_y=None, scale=1.0):
    if offset_y is None:
        offset_x += (screen.get_width() - (WIDTH * 2 + GAP)) // 2
        offset_y = (screen.get_height() - (HEIGHT + EXTRA_HEIGHT)) // 2
    for y, row in enumerate(piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    offset_x + (piece['x'] + x) * BLOCK_SIZE * scale,
                    offset_y + (piece['y'] + y) * BLOCK_SIZE * scale,
                    BLOCK_SIZE * scale,
                    BLOCK_SIZE * scale
                )
                pygame.draw.rect(screen, colors[piece['type']], rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

def check_collision(grid, piece):
    for y, row in enumerate(piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                px = piece['x'] + x
                py = piece['y'] + y
                if px < 0 or px >= COLS or py >= ROWS or (py >= 0 and grid[py][px]):
                    return True
    return False

def lock_piece(grid, piece):
    for y, row in enumerate(piece['shape']):
        for x, cell in enumerate(row):
            if cell:
                py = piece['y'] + y
                px = piece['x'] + x
                if 0 <= py < ROWS and 0 <= px < COLS:
                    grid[py][px] = piece['type']

def rotate(piece):
    piece['shape'] = [list(row) for row in zip(*piece['shape'][::-1])]

def add_garbage_lines(grid, count):
    for _ in range(count):
        grid.pop(0)
        hole = random.randint(0, COLS - 1)
        row = ['X' if i != hole else '' for i in range(COLS)]
        grid.append(row)

def clear_lines(grid, opponent):
    new_grid = []
    cleared = 0
    for row in grid:
        if all(cell != '' for cell in row):
            cleared += 1
        else:
            new_grid.append(row)
    while len(new_grid) < ROWS:
        new_grid.insert(0, [''] * COLS)
    for y in range(ROWS):
        grid[y] = new_grid[y]

    if cleared >= 2:
        add_garbage_lines(opponent.grid, cleared)
    return cleared

class Player:
    def __init__(self, offset_x):
        self.offset_x = offset_x
        self.grid = create_grid()
        self.piece = random_piece()
        self.score = 0
        self.game_over = False

    def spawn(self):
        self.piece = random_piece()
        if check_collision(self.grid, self.piece):
            self.game_over = True

    def move(self, dx):
        self.piece['x'] += dx
        if check_collision(self.grid, self.piece):
            self.piece['x'] -= dx

    def rotate(self):
        old_shape = self.piece['shape']
        rotate(self.piece)
        if check_collision(self.grid, self.piece):
            for dx in [-1, 1, -2, 2]:
                self.piece['x'] += dx
                if not check_collision(self.grid, self.piece):
                    return
                self.piece['x'] -= dx
            self.piece['shape'] = old_shape

    def drop(self, opponent):
        self.piece['y'] += 1
        self.score += 1
        if check_collision(self.grid, self.piece):
            self.piece['y'] -= 1
            if self.piece['y'] <= 0:
                self.game_over = True
            else:
                lock_piece(self.grid, self.piece)
                cleared = clear_lines(self.grid, opponent)
                self.score += [0, 100, 300, 500, 800][cleared]
                self.spawn()

    def hard_drop(self, opponent):
        while not check_collision(self.grid, self.piece):
            self.piece['y'] += 1
            self.score += 1
        self.piece['y'] -= 1
        lock_piece(self.grid, self.piece)
        cleared = clear_lines(self.grid, opponent)
        self.score += [0, 100, 300, 500, 800][cleared]
        self.spawn()

class DemoPlayer(Player):
    def __init__(self, offset_x):
        super().__init__(offset_x)
        self.drop_timer = pygame.time.get_ticks()

    def auto_play(self):
        # Try a move or rotation randomly
        if random.random() < 0.05:
            self.rotate()
        elif random.random() < 0.5:
            self.move(random.choice([-1, 1]))

        # Simulate gravity drop every 500ms
        now = pygame.time.get_ticks()
        if now - self.drop_timer > 500:
            self.drop(self)  # Drop onto itself – no garbage lines in demo
            self.drop_timer = now


def draw_text(text, center_x, center_y, size=48, colour=(255,255,255)):
    f = pygame.font.SysFont("Arial", size)
    surf = f.render(text, True, colour)
    rect = surf.get_rect(center=(center_x, center_y))
    screen.blit(surf, rect)

def countdown(seconds=3):
    for i in range(seconds, 0, -1):
        screen.fill((0,0,0))
        draw_text(f"{i}", screen.get_width()//2, screen.get_height()//2)
        pygame.display.flip()
        time.sleep(1)

def game_loop():
    clock = pygame.time.Clock()

    # === Menu ===
    selected_time = None
    demo_p1 = DemoPlayer(0)
    demo_p2 = DemoPlayer(WIDTH + GAP)
    last_demo_update = pygame.time.get_ticks()

    while selected_time is None:
        screen.fill((10, 10, 10))
        draw_text("2-Player Tetris", screen.get_width() // 2, 40, size=36)
        draw_text("Press 1–5 to select game time", screen.get_width() // 2, 90, size=24)
        draw_text("1 = 30s   2 = 60s   3 = 90s   4 = 120s   5 = 180s", screen.get_width() // 2, 120, size=20)
        draw_text("Player 1: A/D = Move, W = Rotate, S = Drop", screen.get_width() // 2, 170, size=20)
        draw_text("Player 2: ←/→ = Move, ↑ = Rotate, ↓ = Drop", screen.get_width() // 2, 200, size=20)
        draw_text("Tap Drop = soft drop, Hold = hard drop", screen.get_width() // 2, 230, size=20)
        demo_scale = 0.5
        demo_height = int(ROWS * BLOCK_SIZE * demo_scale)
        demo_offset_y = screen.get_height() - demo_height - 10

        draw_text("Press 1–5 to begin", screen.get_width() // 2, demo_offset_y - 30, size=24)

        # Run and draw demo players in a small window at the bottom
        demo_p1.auto_play()
        demo_p2.auto_play()

        demo_scale = 0.5
        demo_offset_y = screen.get_height() - int(ROWS * BLOCK_SIZE * demo_scale) - 10
        demo_offset_x1 = screen.get_width() // 2 - int((COLS * BLOCK_SIZE * demo_scale) + GAP // 2)
        demo_offset_x2 = screen.get_width() // 2 + GAP // 2

        draw_grid(demo_p1.grid, demo_offset_x1, demo_offset_y, demo_scale)
        draw_grid(demo_p2.grid, demo_offset_x2, demo_offset_y, demo_scale)
        if not demo_p1.game_over:
            draw_piece(demo_p1.piece, demo_offset_x1, demo_offset_y, demo_scale)
        if not demo_p2.game_over:
            draw_piece(demo_p2.piece, demo_offset_x2, demo_offset_y, demo_scale)

        pygame.display.flip()
        pygame.time.delay(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_time = 30
                elif event.key == pygame.K_2:
                    selected_time = 60
                elif event.key == pygame.K_3:
                    selected_time = 90
                elif event.key == pygame.K_4:
                    selected_time = 120
                elif event.key == pygame.K_5:
                    selected_time = 180

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: selected_time = 30
                elif event.key == pygame.K_2: selected_time = 60
                elif event.key == pygame.K_3: selected_time = 90
                elif event.key == pygame.K_4: selected_time = 120
                elif event.key == pygame.K_5: selected_time = 180

    p1 = Player(0)
    p2 = Player(WIDTH + GAP)
    start_time = time.time()
    game_over = False
    last_gravity_time = pygame.time.get_ticks()
    game_duration = selected_time
    countdown(3)

    down_keys = {pygame.K_s: None, pygame.K_DOWN: None}
    HOLD_THRESHOLD = 300

    while True:
        screen.fill((20, 20, 20))
        elapsed = int(time.time() - start_time)
        remaining = max(0, game_duration - elapsed)

        if (remaining == 0 or (p1.game_over and p2.game_over)) and not game_over:
            game_over = True
            winner = "Draw"
            if p1.score > p2.score: winner = "Player 1 Wins!"
            elif p2.score > p1.score: winner = "Player 2 Wins!"

        if game_over:
            draw_text("Game Over", screen.get_width()//2, HEIGHT//2 - 80)
            draw_text(winner, screen.get_width()//2, HEIGHT//2 - 40, size=36)
            draw_text(f"Player 1 Score: {p1.score}", screen.get_width()//2, HEIGHT//2, size=24)
            draw_text(f"Player 2 Score: {p2.score}", screen.get_width()//2, HEIGHT//2 + 30, size=24)
            draw_text("Press R to restart", screen.get_width()//2, HEIGHT//2 + 70, size=24)

        if not game_over:
            draw_grid(p1.grid, p1.offset_x)
            draw_grid(p2.grid, p2.offset_x)
            if not p1.game_over: draw_piece(p1.piece, p1.offset_x)
            if not p2.game_over: draw_piece(p2.piece, p2.offset_x)

            text_offset_y = (screen.get_height() - (HEIGHT + EXTRA_HEIGHT)) // 2 + HEIGHT + 20
            draw_text(f"P1: {p1.score}", p1.offset_x + (screen.get_width() - (WIDTH * 2 + GAP)) // 2 + WIDTH//2, text_offset_y, size=20)
            draw_text(f"P2: {p2.score}", p2.offset_x + (screen.get_width() - (WIDTH * 2 + GAP)) // 2 + WIDTH//2, text_offset_y, size=20)
            draw_text(f"Time Left: {remaining}s", screen.get_width()//2, text_offset_y + 30, size=24)

        pygame.display.flip()
        clock.tick(FPS)

        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            elif event.type == pygame.KEYDOWN:
                if game_over and event.key == pygame.K_r:
                    return game_loop()
                if not game_over:
                    if event.key == pygame.K_a: p1.move(-1)
                    elif event.key == pygame.K_d: p1.move(1)
                    elif event.key == pygame.K_w: p1.rotate()
                    elif event.key == pygame.K_s: down_keys[pygame.K_s] = pygame.time.get_ticks()
                    elif event.key == pygame.K_LEFT: p2.move(-1)
                    elif event.key == pygame.K_RIGHT: p2.move(1)
                    elif event.key == pygame.K_UP: p2.rotate()
                    elif event.key == pygame.K_DOWN: down_keys[pygame.K_DOWN] = pygame.time.get_ticks()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_s and down_keys[pygame.K_s] is not None:
                    if pygame.time.get_ticks() - down_keys[pygame.K_s] < HOLD_THRESHOLD:
                        p1.drop(p2)
                    down_keys[pygame.K_s] = None
                elif event.key == pygame.K_DOWN and down_keys[pygame.K_DOWN] is not None:
                    if pygame.time.get_ticks() - down_keys[pygame.K_DOWN] < HOLD_THRESHOLD:
                        p2.drop(p1)
                    down_keys[pygame.K_DOWN] = None

        for key in down_keys:
            if down_keys[key] is not None and now - down_keys[key] >= HOLD_THRESHOLD:
                if key == pygame.K_s and not p1.game_over:
                    p1.hard_drop(p2)
                elif key == pygame.K_DOWN and not p2.game_over:
                    p2.hard_drop(p1)
                down_keys[key] = None

        if not game_over and now - last_gravity_time > GRAVITY_DELAY:
            if not p1.game_over:
                p1.drop(p2)
            if not p2.game_over:
                p2.drop(p1)
            last_gravity_time = now

if __name__ == "__main__":
    game_loop()
