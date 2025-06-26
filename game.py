import pygame
import random

pygame.init()
pygame.mixer.init()

WIDTH = 800
HEIGHT = 600
TILE = 40
COLS = 15
ROWS = HEIGHT // TILE
MAP_WIDTH = TILE * COLS  # 15 coloane pentru hartă
INFO_WIDTH = WIDTH - MAP_WIDTH  # restul pt info (200 px)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomberman")

# Culori
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
IMMORTAL_COLOR = (255, 255, 255)

# Load images
cat1_img = pygame.image.load("cat1.png").convert_alpha()
cat2_img = pygame.image.load("cat2.png").convert_alpha()
cat3_img = pygame.image.load("cat3.png").convert_alpha()
cat4_img = pygame.image.load("cat4.png").convert_alpha()
dog1_img = pygame.image.load("dog1.png").convert_alpha()
dog2_img = pygame.image.load("dog2.png").convert_alpha()

cat1_img = pygame.transform.scale(cat1_img, (TILE, TILE))
cat2_img = pygame.transform.scale(cat2_img, (TILE, TILE))
cat3_img = pygame.transform.scale(cat3_img, (TILE, TILE))
cat4_img = pygame.transform.scale(cat4_img, (TILE, TILE))
dog1_img = pygame.transform.scale(dog1_img, (TILE, TILE))
dog2_img = pygame.transform.scale(dog2_img, (TILE, TILE))

# Încarcă sunete (pune fișierele .wav în același director)
try:
    sound_bomb_placed = pygame.mixer.Sound("bomb_place.wav")
    sound_explosion = pygame.mixer.Sound("bomb-explosion.wav")
    sound_player_hit = pygame.mixer.Sound("player_hit.wav")
    sound_game_over = pygame.mixer.Sound("finish.wav")
except Exception as e:
    print("Eroare la încărcarea sunetelor:", e)
    sound_bomb_placed = None
    sound_explosion = None
    sound_player_hit = None
    sound_game_over = None

def play_sound(sound):
    if sound:
        sound.play()

def generate_map():
    grid = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            r = random.random()
            if r < 0.3:
                row.append('x')  # perete indestructibil
            elif random.random() < 0.3:
                if random.random() < 0.1:
                    row.append('b')  # perete destructibil cu bombă ascunsă
                else:
                    row.append('d')  # perete destructibil normal
            else:
                row.append(' ')  # gol
        grid.append(row)
    return grid

class Explosion:
    def __init__(self, x, y, duration=30):
        self.x = x
        self.y = y
        self.timer = duration

    def update(self):
        self.timer -= 1
        return self.timer <= 0

    def draw(self):
        rect = pygame.Rect(self.x * TILE, self.y * TILE, TILE, TILE)
        pygame.draw.rect(screen, (255, 100, 0), rect)

class Bomb:
    def __init__(self, x, y, owner, power=1, timer=120):
        self.x = x
        self.y = y
        self.owner = owner
        self.timer = timer
        self.power = power

    def update(self):
        self.timer -= 1
        return self.timer <= 0

    def draw(self):
        rect = pygame.Rect(self.x * TILE + 10, self.y * TILE + 10, TILE - 20, TILE - 20)
        pygame.draw.ellipse(screen, (0, 0, 0), rect)

class Bonus:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind  # 'hp', 'power', 'immortal'

    def draw(self):
        if self.kind == 'hp':
            color = (0, 255, 0)
        elif self.kind == 'power':
            color = (255, 0, 255)
        else:  # immortal
            color = (0, 255, 255)
        pygame.draw.rect(screen, color, (self.x * TILE + 10, self.y * TILE + 10, TILE - 20, TILE - 20))
# bonus verde - creste viata jucatorului cu 1
# bonus mov - creste puterea bombei cu 1
# bonus cyan - imunitate temporara

class Player:
    def __init__(self, x, y, color, controls, image=None):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * TILE
        self.pixel_y = y * TILE
        self.color = color
        self.controls = controls
        self.bombs = []
        self.hp = 3
        self.power = 1
        self.immortal = False
        self.immortal_timer = 0
        self.immortal_uses = 1
        self.speed = 5  # pixeli pe frame
        self.score = 0
        self.image = image

    def activate_immortal(self, duration=300):
        self.immortal = True
        self.immortal_timer = duration

    def update(self):
        # Mișcare cursivă către țintă
        target_x = self.grid_x * TILE
        target_y = self.grid_y * TILE

        if self.pixel_x < target_x:
            self.pixel_x = min(self.pixel_x + self.speed, target_x)
        elif self.pixel_x > target_x:
            self.pixel_x = max(self.pixel_x - self.speed, target_x)

        if self.pixel_y < target_y:
            self.pixel_y = min(self.pixel_y + self.speed, target_y)
        elif self.pixel_y > target_y:
            self.pixel_y = max(self.pixel_y - self.speed, target_y)

        if self.immortal:
            self.immortal_timer -= 1
            if self.immortal_timer <= 0:
                self.immortal = False

    def draw(self):
        if self.image:
            screen.blit(self.image, (self.pixel_x, self.pixel_y))
        else:
            center = (int(self.pixel_x) + TILE // 2, int(self.pixel_y) + TILE // 2)
            radius = TILE // 2 - 5
            color = IMMORTAL_COLOR if self.immortal else self.color
            pygame.draw.circle(screen, color, center, radius)

    def move(self, dx, dy, grid):
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS:
            if grid[new_y][new_x] == ' ':
                self.grid_x = new_x
                self.grid_y = new_y


class NPC(Player):
    def __init__(self, x, y, color, image=None):
        super().__init__(x, y, color, {}, image=image)
        self.move_cooldown = 0
        self.move_interval = 45
        self.bomb_cooldown = 0  # cooldown pentru bombe
        self.immortal_uses = 0  # număr de bonusuri de imortalitate colectate

    def update(self, grid, target_players, all_bombs):
        super().update()

        if self.move_cooldown > 0:
            self.move_cooldown -= 1
        else:
            best_move = (0, 0)
            min_dist = float('inf')
            min_danger = float('inf')
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

            for dx, dy in directions:
                nx, ny = self.grid_x + dx, self.grid_y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] == ' ':
                    # Distanța față de cel mai apropiat jucător
                    dist = min(abs(nx - p.grid_x) + abs(ny - p.grid_y) for p in target_players)
                    danger = danger_score(nx, ny, all_bombs)
                    if danger < min_danger or (danger == min_danger and dist < min_dist):
                        best_move = (dx, dy)
                        min_danger = danger
                        min_dist = dist

            if best_move != (0, 0):
                self.move(*best_move, grid)
                self.move_cooldown = self.move_interval

        # Bombe (cu evitarea plasării prea aproape)
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1
        elif random.random() < 0.1 and not any(b.x == self.grid_x and b.y == self.grid_y for b in self.bombs):
            self.bombs.append(Bomb(self.grid_x, self.grid_y, self, power=self.power))
            self.bomb_cooldown = 120
            play_sound(sound_bomb_placed)


def danger_score(x, y, bombs):
    score = 0
    for bomb in bombs:
        if (x, y) == (bomb.x, bomb.y):
            score += 100  # bombă pe poziție
        elif abs(x - bomb.x) + abs(y - bomb.y) <= bomb.power:
            score += 50  # în raza exploziei
    return score

grid = generate_map()
bonuses = []
players = []
explosion_effects = []
game_running = False
selected_players_count = 1  # inițial 1 jucător

def get_random_empty_position(grid, taken_positions):
    while True:
        x = random.randint(0, COLS - 1)
        y = random.randint(0, ROWS - 1)
        if grid[y][x] == ' ' and (x, y) not in taken_positions:
            return x, y

# Golește zona din jurul jucătorilor
for dy in range(2):
    for dx in range(2):
        grid[1 + dy][1 + dx] = ' '
        grid[ROWS - 2 - dy][COLS - 2 - dx] = ' '

p1 = Player(1, 1, (0, 0, 255), {
    pygame.K_w: (0, -1), pygame.K_s: (0, 1),
    pygame.K_a: (-1, 0), pygame.K_d: (1, 0),
    pygame.K_q: 'bomb', pygame.K_z: 'immortal'
}, image=cat1_img)

p2 = Player(COLS - 2, ROWS - 2, (255, 0, 0), {
    pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
    pygame.K_RETURN: 'bomb', pygame.K_m: 'immortal'
}, image=cat2_img)

p3 = Player(1, ROWS - 2, (0, 255, 0), {
    pygame.K_i: (0, -1), pygame.K_k: (0, 1),
    pygame.K_j: (-1, 0), pygame.K_l: (1, 0),
    pygame.K_u: 'bomb', pygame.K_o: 'immortal'
}, image=cat3_img)

p4 = Player(COLS - 2, 1, (128, 0, 128), {
    pygame.K_t: (0, -1), pygame.K_g: (0, 1),
    pygame.K_f: (-1, 0), pygame.K_h: (1, 0),
    pygame.K_r: 'bomb', pygame.K_v: 'immortal'
}, image=cat4_img)

npc1 = NPC(COLS // 2 - 2, ROWS // 2, (0, 200, 0), image=dog1_img)
npc2 = NPC(COLS // 2 + 2, ROWS // 2, (200, 0, 200), image=dog2_img)

paused = False
clock = pygame.time.Clock()

game_timer = 0

MAX_GAME_TIME = 120 * 60  # 2a minute la 60 FPS
obstacle_layer_index = 0  # pentru poziția curentă a înlocuirii circulare
obstacle_positions = []   # lista pozițiilor pe marginea hărții pentru plasare obstacole

cat1_img = pygame.image.load("cat1.png").convert_alpha()
cat1_img = pygame.transform.scale(cat1_img, (TILE, TILE))
cat2_img = pygame.image.load("cat2.png").convert_alpha()
cat2_img = pygame.transform.scale(cat2_img, (TILE, TILE))
cat3_img = pygame.image.load("cat3.png").convert_alpha()
cat3_img = pygame.transform.scale(cat1_img, (TILE, TILE))
cat4_img = pygame.image.load("cat4.png").convert_alpha()
cat4_img = pygame.transform.scale(cat2_img, (TILE, TILE))

img_wall_x = pygame.image.load("wall_indestructible.png").convert()
img_wall_d = pygame.image.load("wall_destructible.png").convert()
img_wall_x = pygame.transform.scale(img_wall_x, (TILE, TILE))
img_wall_d = pygame.transform.scale(img_wall_d, (TILE, TILE))

def generate_spiral_positions(cols, rows):
    positions = []
    start_x, start_y = 0, 0
    end_x, end_y = cols - 1, rows - 1

    while start_x <= end_x and start_y <= end_y:
        # Parcurgem dreapta (pe linia start_y)
        for x in range(start_x, end_x + 1):
            positions.append((x, start_y))
        start_y += 1

        # Parcurgem jos (pe coloana end_x)
        for y in range(start_y, end_y + 1):
            positions.append((end_x, y))
        end_x -= 1

        if start_y <= end_y:
            # Parcurgem stanga (pe linia end_y)
            for x in range(end_x, start_x - 1, -1):
                positions.append((x, end_y))
            end_y -= 1

        if start_x <= end_x:
            # Parcurgem sus (pe coloana start_x)
            for y in range(end_y, start_y - 1, -1):
                positions.append((start_x, y))
            start_x += 1

    return positions

obstacle_positions = generate_spiral_positions(COLS, ROWS)
human_players_initial = [p1, p2, p3, p4][:selected_players_count]  # lista jucători umani la start

while True:
    clock.tick(60)
    if game_running and not paused:
        game_timer += 1
        if game_timer >= MAX_GAME_TIME:
            pos = obstacle_positions[obstacle_layer_index]
            x, y = pos

            if grid[y][x] != 'x':
                grid[y][x] = 'x'
                for player in players:
                    if player.grid_x == x and player.grid_y == y:
                        player.hp = 0  # moare instant

            obstacle_layer_index += 1
            if obstacle_layer_index >= len(obstacle_positions):
                obstacle_layer_index = 0

            obstacle_layer_index += 1
            if obstacle_layer_index >= len(obstacle_positions):
                obstacle_layer_index = 0  # resetăm ciclul dacă vrem să continuăm în cerc

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if not game_running:
                if event.key == pygame.K_LEFT:
                    selected_players_count = max(1, selected_players_count - 1)
                elif event.key == pygame.K_RIGHT:
                    selected_players_count = min(4, selected_players_count + 1)
                elif event.key == pygame.K_RETURN:
                    taken_positions = set()
                    game_running = True
                    players.clear()
                    taken_positions = set()
                    # P1
                    x1, y1 = get_random_empty_position(grid, taken_positions)
                    taken_positions.add((x1, y1))
                    p1.grid_x, p1.grid_y = x1, y1
                    p1.pixel_x, p1.pixel_y = x1 * TILE, y1 * TILE
                    players.append(p1)

                    if selected_players_count >= 2:
                        x2, y2 = get_random_empty_position(grid, taken_positions)
                        taken_positions.add((x2, y2))
                        p2.grid_x, p2.grid_y = x2, y2
                        p2.pixel_x, p2.pixel_y = x2 * TILE, y2 * TILE
                        players.append(p2)

                    if selected_players_count >= 3:
                        x3, y3 = get_random_empty_position(grid, taken_positions)
                        taken_positions.add((x3, y3))
                        p3.grid_x, p3.grid_y = x3, y3
                        p3.pixel_x, p3.pixel_y = x3 * TILE, y3 * TILE
                        players.append(p3)

                    if selected_players_count >= 4:
                        x4, y4 = get_random_empty_position(grid, taken_positions)
                        taken_positions.add((x4, y4))
                        p4.grid_x, p4.grid_y = x4, y4
                        p4.pixel_x, p4.pixel_y = x4 * TILE, y4 * TILE
                        players.append(p4)

                    # NPCs
                    if selected_players_count == 3:
                        xn1, yn1 = get_random_empty_position(grid, taken_positions)
                        taken_positions.add((xn1, yn1))
                        npc1.grid_x, npc1.grid_y = xn1, yn1
                        npc1.pixel_x, npc1.pixel_y = xn1 * TILE, yn1 * TILE
                        players.append(npc1)
                    elif selected_players_count == 4:
                        xn1, yn1 = get_random_empty_position(grid, taken_positions)
                        xn2, yn2 = get_random_empty_position(grid, taken_positions | {(xn1, yn1)})
                        npc1.grid_x, npc1.grid_y = xn1, yn1
                        npc1.pixel_x, npc1.pixel_y = xn1 * TILE, yn1 * TILE
                        npc2.grid_x, npc2.grid_y = xn2, yn2
                        npc2.pixel_x, npc2.pixel_y = xn2 * TILE, yn2 * TILE
                        taken_positions.add((xn1, yn1))
                        taken_positions.add((xn2, yn2))
                        players.append(npc1)
                        players.append(npc2)


                    # Reset poziții jucători

                    p1.pixel_x, p1.pixel_y = p1.grid_x * TILE, p1.grid_y * TILE
                    p2.pixel_x, p2.pixel_y = p2.grid_x * TILE, p2.grid_y * TILE
                    if selected_players_count == 3:
                        npc1.grid_x, npc1.grid_y = COLS // 2, ROWS // 2
                        npc1.pixel_x, npc1.pixel_y = npc1.grid_x * TILE, npc1.grid_y * TILE
                    elif selected_players_count == 4:
                        npc1.grid_x, npc1.grid_y = COLS // 2 - 2, ROWS // 2
                        npc1.pixel_x, npc1.pixel_y = npc1.grid_x * TILE, npc1.grid_y * TILE
                        npc2.grid_x, npc2.grid_y = COLS // 2 + 2, ROWS // 2
                        npc2.pixel_x, npc2.pixel_y = npc2.grid_x * TILE, npc2.grid_y * TILE

                    human_players_initial = []
                    if selected_players_count >= 1:
                        human_players_initial.append(p1)
                    if selected_players_count >= 2:
                        human_players_initial.append(p2)
                    if selected_players_count >= 3:
                        human_players_initial.append(p3)
                    if selected_players_count >= 4:
                        human_players_initial.append(p4)

                    bonuses.clear()
                    explosion_effects.clear()
                    paused = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
            else:
                # În joc: ESC oprește și revine la meniu
                if event.key == pygame.K_ESCAPE:
                    game_running = False
                else:
                    if not paused:
                        for player in players:
                            if event.key in player.controls:
                                action = player.controls[event.key]
                                if action == 'bomb':
                                    can_place = True
                                    for bomb in player.bombs:
                                        if bomb.x == player.grid_x and bomb.y == player.grid_y:
                                            can_place = False
                                            break
                                    if can_place:
                                        bomb = Bomb(player.grid_x, player.grid_y, player, power=player.power)
                                        player.bombs.append(bomb)
                                        play_sound(sound_bomb_placed)

                                elif action == 'immortal':
                                    if player.immortal_uses > 0 and not player.immortal:
                                        player.activate_immortal(300)  # 5 secunde = 300 frame-uri la 60 FPS
                                        player.immortal_uses -= 1

                                else:
                                    dx, dy = action
                                    player.move(dx, dy, grid)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused

    if not game_running:
        screen.fill(BLACK)
        font = pygame.font.SysFont("Arial", 40)
        text = font.render("Select number of players (1-4): " + str(selected_players_count), True, WHITE)
        info_lines = [
            "Jucător 1 (Albastru): W A S D - mișcare, Q - bombă",
            "Jucător 2 (Roșu): <- ^ -> v, ENTER - bombă",
            "Jucător 3 (Verde): I J K L - mișcare, U - bombă",
            "Jucător 4 (Mov): T F G H - mișcare, R - bombă",
        ]
        screen.blit(text, (20, HEIGHT // 2))
        font_small = pygame.font.SysFont("Arial", 25)
        screen.blit(font_small.render("Left/Right to change, Enter to start", True, WHITE), (20, HEIGHT // 2 + 50))
        pygame.display.flip()
        continue

    if paused:
        font = pygame.font.SysFont("Arial", 50)
        screen.blit(font.render("PAUSED", True, YELLOW), (MAP_WIDTH // 2 - 80, HEIGHT // 2))
        pygame.display.flip()
        continue

    # Update jucători
    for player in players:
        if isinstance(player, NPC):
            player.update(grid, [p for p in players if not isinstance(p, NPC)], [b for p in players for b in p.bombs])
        else:
            player.update()

    # Update bombe
    exploded_bombs = []
    for player in players:
        for bomb in player.bombs:
            if bomb.update():
                exploded_bombs.append((bomb, player))
    # Explozie bombe
    for bomb, owner in exploded_bombs:
        play_sound(sound_explosion)
        owner.bombs.remove(bomb)
        explosion_effects.append(Explosion(bomb.x, bomb.y))

        # Explozie în sus, jos, stânga, dreapta după puterea bombei
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            for p in range(1, bomb.power + 1):
                ex = bomb.x + dx * p
                ey = bomb.y + dy * p
                if 0 <= ex < COLS and 0 <= ey < ROWS:
                    if grid[ey][ex] == 'x':  # perete indestructibil
                        break
                    explosion_effects.append(Explosion(ex, ey))
                    if grid[ey][ex] in ('d', 'b'):
                        is_trap = (grid[ey][ex] == 'b')
                        grid[ey][ex] = ' '
                        owner.score += 10
                        if is_trap:
                            # Activează bomba-capcană imediat
                            trap_bomb = Bomb(ex, ey, owner, power=1, timer=30)  # explodează rapid
                            owner.bombs.append(trap_bomb)
                        else:
                            if random.random() < 0.3:
                                kind = random.choice(['hp', 'power', 'immortal'])
                                bonuses.append(Bonus(ex, ey, kind))
                        break
                else:
                    break

    # Update explozie
    explosion_effects = [e for e in explosion_effects if not e.update()]

    # Verifică coliziuni explozie - jucători
    for e in explosion_effects:
        for player in players:
            if player.grid_x == e.x and player.grid_y == e.y and not player.immortal:
                player.hp -= 1
                player.activate_immortal()
                play_sound(sound_player_hit)

    # Colectare bonus
    for bonus in bonuses[:]:
        for player in players:
            if player.grid_x == bonus.x and player.grid_y == bonus.y:
                if bonus.kind == 'hp':
                    player.hp += 1
                elif bonus.kind == 'power':
                    player.power += 1
                else:  # immortal
                    player.immortal_uses += 1  # colectează dar NU activează imediat
                bonuses.remove(bonus)

    # Șterge jucătorii morți
    alive_players = []
    for p in players:
        if p.hp <= 0:
            play_sound(sound_player_hit)  # sunet eliminare
        else:
            alive_players.append(p)
    players = alive_players
    # Verifică dacă toți jucătorii umani sunt morți
    if not any(not isinstance(p, NPC) and p.hp > 0 for p in players):  # toți jucătorii umani morți
        play_sound(sound_game_over)
        font_large = pygame.font.SysFont("Arial", 80)
        font_small = pygame.font.SysFont("Arial", 30)
        screen.fill(BLACK)

        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 150))

        # Sortează jucătorii după scor, descrescător
        sorted_humans = sorted(human_players_initial, key=lambda p: p.score, reverse=True)

        y_offset = HEIGHT // 2 - 50
        for i, player in enumerate(sorted_humans):
            text = f"Player {i + 1} Score: {player.score}"
            label = font_small.render(text, True, player.color)
            screen.blit(label, (WIDTH // 2 - label.get_width() // 2, y_offset))
            y_offset += 40

        if sorted_humans:
            winner = sorted_humans[0]
            winner_index = human_players_initial.index(winner) + 1
            winner_text = f"Winner: Player {winner_index}!"
            winner_label = font_large.render(winner_text, True, winner.color)
            screen.blit(winner_label, (WIDTH // 2 - winner_label.get_width() // 2, y_offset + 20))

        pygame.display.flip()
        pygame.time.delay(5000)
        game_running = False
        continue

    # Coliziuni: NPC lovește jucător uman la contact
    for npc in players:
        if isinstance(npc, NPC):
            for player in players:
                if not isinstance(player, NPC) and player.hp > 0 and not player.immortal:
                    if npc.grid_x == player.grid_x and npc.grid_y == player.grid_y:
                        player.hp = 0
                        play_sound(sound_player_hit)

    # Desenează harta
    screen.fill(BLACK)
    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
            if grid[y][x] == 'x':
                screen.blit(img_wall_x, rect)
            elif grid[y][x] in ('d', 'b'):
                screen.blit(img_wall_d, rect)
            else:
                pygame.draw.rect(screen, (50, 50, 50), rect)  # fundal

    # Desenează bombe
    for player in players:
        for bomb in player.bombs:
            bomb.draw()

    # Desenează explozie
    for e in explosion_effects:
        e.draw()

    # Desenează bonusuri
    for bonus in bonuses:
        bonus.draw()

    # Desenează jucători
    for player in players:
        player.draw()

    # Desenează info în partea dreaptă
    pygame.draw.rect(screen, (20, 20, 20), (MAP_WIDTH, 0, INFO_WIDTH, HEIGHT))
    font = pygame.font.SysFont("Arial", 15)
    y_off = 20
    for i, player in enumerate(players):
        text = f"P{i+1} HP:{player.hp} Pow:{player.power} Imm:{player.immortal_uses} Score:{player.score}"
        label = font.render(text, True, player.color)
        screen.blit(label, (MAP_WIDTH + 10, y_off))
        y_off += 40
    timer_seconds = game_timer // 60
    timer_label = font.render(f"Time: {timer_seconds}s", True, WHITE)
    screen.blit(timer_label, (MAP_WIDTH + 10, y_off + 20))


    pygame.display.flip()
