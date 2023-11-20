import pygame
import math
from enum import Enum


# Part Type
class PT(Enum):
    BLANK = 0
    PLAYER = 1
    BRICK = 2
    BACKGROUND = 3
    CEMENT = 4
    ENEMY = 5


BLOCK_SIZE = 20
BLOCK_MARGIN = 1
all_parts = {}
PART_COLOR = {PT.BRICK: "brown", PT.BACKGROUND: pygame.Color(0, 156, 252), PT.PLAYER: "orange",
              PT.CEMENT: pygame.Color(201, 201, 201)}
PLAYER_COLOR = {"head": "orange", "pants": pygame.Color(40, 93, 191), "shoes": "black",
                "skin": pygame.Color(212, 157, 99), "belt": "black", "shirt": pygame.Color(124, 100, 232)}
PLAYER_VELOCITY = {"normal": 10, "crouch": 7}
PLAYER_JUMP_H = {"normal": 4, "crouch": 2}

WIDTH, HEIGHT = 1280, 720
W_BLOCKS, H_BLOCKS = WIDTH // BLOCK_SIZE, HEIGHT // BLOCK_SIZE
e = 0.1


class Direction(Enum):
    FRONT = 0
    LEFT = 1
    RIGHT = 2


class Part:

    def __init__(self, x: int, y: int, pt: PT):
        self.pt = pt
        self.color = PART_COLOR.get(pt)
        all_parts[(x, y)] = self


class Game:

    def __init__(self, width: int, height: int):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Pizza Boi")

        self.player_position = [W_BLOCKS // 2, H_BLOCKS - 3]
        self.player_velocity = PLAYER_VELOCITY.get("normal")
        self.player_crouch = False
        self.player_stuck = [False, False, False]  # [from_left, from_right, from_top]
        self.jump_velocity = 0
        self.player_direction = Direction.FRONT
        self.GRAVITY = 25
        self.jump_height = PLAYER_JUMP_H.get("normal")
        self.init_floor()

        Maps.map_0()

    def handle_keys(self, dt):
        self.player_direction = Direction.FRONT

        keys = pygame.key.get_pressed()
        if not self.player_stuck[2] and (keys[pygame.K_w] or keys[pygame.K_UP]):
            self.jump()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if not self.player_stuck[0]:
                self.player_position[0] -= dt * self.player_velocity
            self.player_direction = Direction.LEFT
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if not self.player_stuck[1]:
                self.player_position[0] += dt * self.player_velocity
            self.player_direction = Direction.RIGHT
        if keys[pygame.K_s] or keys[pygame.K_DOWN] or (self.player_crouch and self.player_stuck[2]):
            self.player_crouch = True
            self.player_velocity = PLAYER_VELOCITY.get("crouch")
            self.jump_height = PLAYER_JUMP_H.get("crouch")
        else:
            self.player_crouch = False
            self.player_velocity = PLAYER_VELOCITY.get("normal")
            self.jump_height = PLAYER_JUMP_H.get("normal")

        self.player_position[0] = round(self.player_position[0], 1)

    def init_floor(self):
        extra_floor = 5
        y_floor = H_BLOCKS - 1
        left_border_x = self.player_position[0] - W_BLOCKS // 2 - extra_floor

        for i in range(W_BLOCKS + 2 * extra_floor):
            Part(left_border_x + i, y_floor, PT.BRICK)
            Part(left_border_x + i, y_floor - 1, PT.BRICK)

    def draw_parts(self):

        left_border_x = self.player_position[0] - W_BLOCKS // 2
        xy_part_map = [(left_border_x + i, y) for i in range(W_BLOCKS + 1) for y in range(0, H_BLOCKS + 1) if
                       all_parts.get((math.floor(left_border_x) + i, y)) is not None]

        for (x, y) in xy_part_map:
            left, top = (x - left_border_x - round(self.player_position[0] % 1, 1)) * BLOCK_SIZE, y * BLOCK_SIZE
            part = all_parts.get((math.floor(x), y))
            if isinstance(part, Part):
                self.draw_part(part.pt, left, top)

    def draw_part(self, pt: PT, left, top):
        w = h = BLOCK_SIZE - 2 * BLOCK_MARGIN
        if pt == PT.BRICK:
            pygame.draw.rect(self.screen, PART_COLOR.get(PT.CEMENT), (left, top, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.screen, PART_COLOR.get(PT.BRICK), (left + BLOCK_MARGIN, top + BLOCK_MARGIN, w, h))

    def draw_player(self):
        size = BLOCK_SIZE
        left, top = (W_BLOCKS // 2) * BLOCK_SIZE, self.player_position[1] * BLOCK_SIZE

        if self.player_crouch:
            size = BLOCK_SIZE // 2
            left += size // 2

        bottom = top + BLOCK_SIZE
        leg_w = size // 5
        leg_h = 3 * (size // 4)
        shoes_h = (size // 6)
        torso_w = 3 * (size // 5)
        torso_h = 3 * (size // 5)
        head_w = 1.5 * (size // 5)

        if self.player_direction == Direction.FRONT:
            # legs
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("pants"),
                             (left + leg_w, (bottom - size) + (size - leg_h), leg_w, leg_h))
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("pants"),
                             (left + 3 * leg_w, (bottom - size) + (size - leg_h), leg_w, leg_h))

            # shoes
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("shoes"),
                             (left + leg_w, (bottom - size) + (size - shoes_h), leg_w, shoes_h))
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("shoes"),
                             (left + 3 * leg_w, (bottom - size) + (size - shoes_h), leg_w, shoes_h))

            # belt
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("belt"),
                             (left + leg_w, (bottom - size), torso_w, (size - leg_h)))
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("pants"), (left + leg_w, (bottom - size) + 2, torso_w, 5))

            # torso
            shoulder_height = (bottom - size) - size + (size - torso_h)
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("shirt"),
                             (left + size // 5, shoulder_height, torso_w, torso_h))

            # head
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("head"),
                             (left + size // 2 - head_w / 2, (bottom - size) - size, head_w, (size - torso_h)))

            # hands
            if self.jump_velocity == 0:
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("skin"), (left, shoulder_height, leg_w, leg_h))
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("shirt"), (left, shoulder_height, leg_w, 5))
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("skin"),
                                 (left + 4 * leg_w, shoulder_height, leg_w, leg_h))
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("shirt"), (left + 4 * leg_w, shoulder_height, leg_w, 5))
            else:
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("skin"),
                                 (left, shoulder_height - leg_h + 5, leg_w, leg_h))
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("shirt"), (left, shoulder_height, leg_w, 5))
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("skin"),
                                 (left + 4 * leg_w, shoulder_height - leg_h + 5, leg_w, leg_h))
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("shirt"), (left + 4 * leg_w, shoulder_height, leg_w, 5))
        else:
            # legs
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("pants"),
                             (left + 2 * leg_w, (bottom - size) + (size - leg_h), leg_w, leg_h))

            # belt
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("belt"),
                             (left + 2 * leg_w, (bottom - size), leg_w, (size - leg_h)))
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("pants"), (left + 2 * leg_w, (bottom - size) + 2, leg_w, 5))

            # torso
            shoulder_height = (bottom - size) - size + (size - torso_h)
            pygame.draw.rect(self.screen, PLAYER_COLOR.get("shirt"),
                             (left + 2 * leg_w, shoulder_height, leg_w, torso_h))

            # hands
            if self.jump_velocity == 0:
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("skin"),
                                 (left + 2 * leg_w, shoulder_height, leg_w, leg_h))
            else:
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("skin"),
                                 (left + 2 * leg_w, shoulder_height - leg_h + 5, leg_w, leg_h))

            if self.player_direction == Direction.RIGHT:
                # shoes
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("shoes"),
                                 (left + 2 * leg_w, (bottom - size) + (size - shoes_h), leg_w + 2, shoes_h))

                # head
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("head"),
                                 (left + 2 * leg_w, (bottom - size) - size, head_w, (size - torso_h)))

            else:  # self.player_direction == Direction.LEFT
                # shoes
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("shoes"),
                                 (left + 2 * leg_w - 2, (bottom - size) + (size - shoes_h), leg_w + 2, shoes_h))

                # head
                pygame.draw.rect(self.screen, PLAYER_COLOR.get("head"),
                                 (
                                     left + 2 * leg_w - (head_w - leg_w), (bottom - size) - size, head_w,
                                     (size - torso_h)))

    def jump(self):
        part_below_1 = all_parts.get((math.floor(self.player_position[0]), self.player_position[1] + 1))
        part_below_2 = all_parts.get((math.ceil(self.player_position[0]), self.player_position[1] + 1))
        if (isinstance(part_below_1, Part) and part_below_1.pt == PT.BRICK) or \
                (isinstance(part_below_2, Part) and part_below_2.pt == PT.BRICK):
            self.jump_velocity = - (2 * self.GRAVITY * self.jump_height) ** 0.5

    def update_player_position(self, dt):
        padding = 7  # in pixels

        # block under the player
        part_below_1 = all_parts.get((math.floor(self.player_position[0]), math.ceil(self.player_position[1] + 1)))
        part_below_2 = all_parts.get((math.ceil(self.player_position[0]), math.ceil(self.player_position[1] + 1)))
        player_padding_below = self.player_position[1] * BLOCK_SIZE + padding
        bounder_line_below = math.ceil(self.player_position[1]) * BLOCK_SIZE

        block_is_below = ((isinstance(part_below_1, Part) and part_below_1.pt == PT.BRICK) or
                          (isinstance(part_below_2, Part) and part_below_2.pt == PT.BRICK)) and \
                         self.jump_velocity >= 0 and \
                         player_padding_below >= bounder_line_below

        if block_is_below:
            self.jump_velocity = 0
            self.player_position[1] = math.ceil(self.player_position[1])

        # apply gravity
        else:
            self.player_position[1] += self.jump_velocity * dt + 0.5 * self.GRAVITY * dt ** 2
            self.jump_velocity += self.GRAVITY * dt

        # block besides the player.
        part_from_right0 = all_parts.get((math.ceil(self.player_position[0]), math.ceil(self.player_position[1])))
        part_from_left0 = all_parts.get((math.floor(self.player_position[0]), math.ceil(self.player_position[1])))
        part_from_right1 = all_parts.get((math.ceil(self.player_position[0]), math.ceil(self.player_position[1] - 1)))
        part_from_left1 = all_parts.get((math.floor(self.player_position[0]), math.ceil(self.player_position[1] - 1)))

        player_padding_right = (self.player_position[0] + 1) * BLOCK_SIZE + 10
        player_padding_left = (self.player_position[0]) * BLOCK_SIZE + 10
        bounder_line_right = (math.ceil(self.player_position[0])) * BLOCK_SIZE
        bounder_line_left = (math.floor(self.player_position[0])) * BLOCK_SIZE

        block_on_right0 = isinstance(part_from_right0, Part) and part_from_right0.pt == PT.BRICK and \
                          player_padding_right >= bounder_line_right
        block_on_left0 = isinstance(part_from_left0, Part) and part_from_left0.pt == PT.BRICK and \
                         player_padding_left >= bounder_line_left
        block_on_right1 = isinstance(part_from_right1, Part) and part_from_right1.pt == PT.BRICK and \
                          player_padding_right >= bounder_line_right
        block_on_left1 = isinstance(part_from_left1, Part) and part_from_left1.pt == PT.BRICK and \
                         player_padding_left >= bounder_line_left

        # player crouch
        if self.player_crouch:
            if block_on_right0:
                self.player_position[0] = math.floor(self.player_position[0])
                self.player_stuck[1] = True

            else:
                self.player_stuck[1] = False

            if block_on_left0:
                self.player_position[0] = math.ceil(self.player_position[0])
                self.player_stuck[0] = True

            else:
                self.player_stuck[0] = False

        # Player don't crouch
        if not self.player_crouch:

            if block_on_right0 or block_on_right1:
                self.player_position[0] = math.floor(self.player_position[0])
                self.player_stuck[1] = True

            else:
                self.player_stuck[1] = False

            if block_on_left0 or block_on_left1:
                self.player_position[0] = math.ceil(self.player_position[0])
                self.player_stuck[0] = True

            else:
                self.player_stuck[0] = False

        # block above the player
        if not self.player_crouch:
            part_above0 = all_parts.get((math.floor(self.player_position[0]), math.floor(self.player_position[1] - 2)))
            part_above1 = all_parts.get((math.ceil(self.player_position[0]), math.floor(self.player_position[1] - 2)))
            above_player_padding = (self.player_position[1] - 1) * BLOCK_SIZE - padding
            above_player_part = math.floor(self.player_position[1] - 1) * BLOCK_SIZE

        else:  # self.player_crouch == True
            part_above0 = all_parts.get((math.floor(self.player_position[0]), math.floor(self.player_position[1] - 1)))
            part_above1 = all_parts.get((math.ceil(self.player_position[0]), math.floor(self.player_position[1] - 1)))
            above_player_padding = (self.player_position[1]) * BLOCK_SIZE - padding
            above_player_part = math.floor(self.player_position[1]) * BLOCK_SIZE

        block_from_above = ((isinstance(part_above0, Part) and part_above0.pt == PT.BRICK) or
                            (isinstance(part_above1, Part) and part_above1.pt == PT.BRICK)) and \
                           self.jump_velocity <= 0 and \
                           above_player_padding <= above_player_part

        if block_from_above:
            self.player_stuck[2] = True
            self.jump_velocity = 0
            self.player_position[1] = math.floor(self.player_position[1])
        else:
            self.player_stuck[2] = False


class Maps:
    def __init__(self):
        self.maps = []

    @staticmethod
    def map_0():
        level_0 = H_BLOCKS - 3
        x, y = W_BLOCKS // 2, level_0
        for i in range(4):
            for j in range(5):
                Part(x + 3 + 5 * i + j, y - i, PT.BRICK)

        Part(x + 50, y, PT.BRICK)
        Part(x + 50, y - 1, PT.BRICK)


def main():
    game = Game(WIDTH, HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        dt = game.clock.tick(60) / 1000

        game.screen.fill(PART_COLOR.get(PT.BACKGROUND))

        game.init_floor()
        game.draw_parts()

        game.handle_keys(dt)
        game.update_player_position(dt)
        game.draw_player()
        pygame.display.flip()


if __name__ == "__main__":
    main()
