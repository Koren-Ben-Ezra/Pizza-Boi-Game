import pygame
import math
from enum import Enum


# Part Type
class PT(Enum):
    BLANK = 0
    PLAYER = 1
    BRICK = 2
    BACKGROUND = 3
    PIZZA = 4
    MINI_PIZZA = 5
    BOX = 6
    ENEMY = 7


BLOCK_SIZE = 20
BLOCK_MARGIN = 1
all_parts = {}
PART_COLOR = {"brick0": pygame.Color(201, 201, 201), "brick1": "brown", "background": pygame.Color(0, 156, 252),
              "box0": pygame.Color(166, 101, 51), "box1": pygame.Color(207, 135, 81)}
PLAYER_COLOR = {"head": "orange", "pants": pygame.Color(40, 93, 191), "shoes": "black",
                "skin": pygame.Color(212, 157, 99), "belt": "black", "shirt": pygame.Color(124, 100, 232)}
PLAYER_VELOCITY = {"normal": 10, "crouch": 7}
PLAYER_JUMP_H = {"normal": 4, "crouch": 2}
BLOCK_PARTS = (PT.BRICK, PT.BOX)
BREAKABLE_BLOCKS = (PT.BOX,)

WIDTH, HEIGHT = 1280, 720
W_BLOCKS, H_BLOCKS = WIDTH // BLOCK_SIZE, HEIGHT // BLOCK_SIZE
e = 0.1


class Direction(Enum):
    FRONT = 0
    LEFT = 1
    RIGHT = 2


class Part:

    def __init__(self, x: int, y: int, pt: PT, lifetime: int = None, direction: Direction = None):
        self.x = x
        self.y = y
        self.pt = pt
        self.lifetime = lifetime
        self.direction = direction
        if not self.pt == PT.PIZZA:
            all_parts[(x, y)] = self


class Game:

    def __init__(self, width: int, height: int):
        pygame.init()
        self.running = True
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Pizza Boi")
        self.player_position = [W_BLOCKS // 2, H_BLOCKS - 3]
        self.player_velocity = PLAYER_VELOCITY.get("normal")
        self.player_crouch = False
        self.player_stuck = [False, False, False]  # [from_left, from_right, from_top]
        self.player_direction = Direction.FRONT
        self.player_jump_height = PLAYER_JUMP_H.get("normal")
        self.player_jump_velocity = 0
        self.pizza_velocity = 20
        self.pizza_lifetime = 1000  # milliseconds
        self.pizza_objects = []
        self.GRAVITY = 25
        self.map = Maps(self)
        self.reset()

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
            self.player_jump_height = PLAYER_JUMP_H.get("crouch")
        else:
            self.player_crouch = False
            self.player_velocity = PLAYER_VELOCITY.get("normal")
            self.player_jump_height = PLAYER_JUMP_H.get("normal")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._throw_pizza()

        self.player_position[0] = round(self.player_position[0], 1)

    def init_floor(self):
        extra_floor = 5
        y_floor = H_BLOCKS - 1
        left_border_x = self.player_position[0] - W_BLOCKS // 2 - extra_floor

        for i in range(W_BLOCKS + 2 * extra_floor):
            Part(left_border_x + i, y_floor, PT.BRICK)
            Part(left_border_x + i, y_floor - 1, PT.BRICK)

    def draw_parts(self):

        left_border_x = math.floor(self.player_position[0] - W_BLOCKS // 2)

        xy_part_map = [(left_border_x + i, y) for i in range(W_BLOCKS + 1) for y in range(0, H_BLOCKS + 1) if
                       all_parts.get((left_border_x + i, y)) is not None]
        for (x, y) in xy_part_map:
            left, top = (x - left_border_x - round(self.player_position[0] % 1, 1)) * BLOCK_SIZE, y * BLOCK_SIZE
            part = all_parts.get((math.floor(x), y))
            if isinstance(part, Part):
                self.draw_part(part.pt, left, top)

        for pizza_part in self.pizza_objects:
            left, top = (pizza_part.x - left_border_x - round(self.player_position[0] % 1,
                                                              1)) * BLOCK_SIZE, pizza_part.y * BLOCK_SIZE
            self.draw_part(pizza_part.pt, left, top)

    def draw_part(self, pt: PT, left, top):
        if pt == PT.BRICK:
            w = h = BLOCK_SIZE - 2 * BLOCK_MARGIN
            pygame.draw.rect(self.screen, PART_COLOR.get("brick0"), (left, top, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.screen, PART_COLOR.get("brick1"), (left + BLOCK_MARGIN, top + BLOCK_MARGIN, w, h))
        if pt == PT.BOX:
            w = h = BLOCK_SIZE - 6 * BLOCK_MARGIN
            pygame.draw.rect(self.screen, PART_COLOR.get("box0"), (left, top, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.screen, PART_COLOR.get("box1"),
                             (left + 3 * BLOCK_MARGIN, top + 3 * BLOCK_MARGIN, w, h))

        if pt == PT.PIZZA:
            pygame.draw.rect(self.screen, "red",
                             (left, top + 10, BLOCK_SIZE, 5))

        if pt == PT.MINI_PIZZA:
            pygame.draw.rect(self.screen, "red", (left, top + 5, BLOCK_SIZE // 2, 3))

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
            if self.player_jump_velocity == 0:
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
            if self.player_jump_velocity == 0:
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
        if (isinstance(part_below_1, Part) and part_below_1.pt in BLOCK_PARTS) or \
                (isinstance(part_below_2, Part) and part_below_2.pt in BLOCK_PARTS):
            self.player_jump_velocity = - (2 * self.GRAVITY * self.player_jump_height) ** 0.5

    def update_pizzas_position(self, dt):
        for pizza_part in self.pizza_objects:

            if pizza_part.lifetime < pygame.time.get_ticks():
                self.pizza_objects.remove(pizza_part)

            elif pizza_part.direction == Direction.RIGHT:
                pizza_part.x += dt * self.pizza_velocity
            else:  # pizza_part.direction == Direction.LEFT
                pizza_part.x -= dt * self.pizza_velocity

        self._update_pizza_collision()

    def _update_pizza_collision(self):
        for pizza_part in self.pizza_objects:
            part_from_right = all_parts.get((math.ceil(pizza_part.x), math.ceil(pizza_part.y)))
            part_from_left = all_parts.get((math.floor(pizza_part.x), math.ceil(pizza_part.y)))
            pizza_padding_right = (pizza_part.x + 1) * BLOCK_SIZE + 10
            pizza_padding_left = pizza_part.x * BLOCK_SIZE + 10
            bounder_line_right = math.ceil(pizza_part.x) * BLOCK_SIZE
            bounder_line_left = math.floor(pizza_part.x) * BLOCK_SIZE

            block_on_right = isinstance(part_from_right, Part) and part_from_right.pt in BLOCK_PARTS and \
                             pizza_padding_right >= bounder_line_right
            block_on_left = isinstance(part_from_left, Part) and part_from_left.pt in BLOCK_PARTS and \
                            pizza_padding_left >= bounder_line_left

            if block_on_right or block_on_left:
                pizza_part.lifetime -= self.pizza_lifetime

            if block_on_right and part_from_right.pt in BREAKABLE_BLOCKS:
                self._break_breakable(math.ceil(pizza_part.x), math.ceil(pizza_part.y))

            if block_on_left and part_from_left.pt in BREAKABLE_BLOCKS:
                self._break_breakable(math.floor(pizza_part.x), math.ceil(pizza_part.y))

    @staticmethod
    def _break_breakable(x, y):
        del all_parts[(x, y)]

    def update_player_position(self, dt):
        padding = 7  # in pixels

        # block under the player
        part_below_1 = all_parts.get((math.floor(self.player_position[0]), math.ceil(self.player_position[1] + 1)))
        part_below_2 = all_parts.get((math.ceil(self.player_position[0]), math.ceil(self.player_position[1] + 1)))
        player_padding_below = self.player_position[1] * BLOCK_SIZE + padding
        bounder_line_below = math.ceil(self.player_position[1]) * BLOCK_SIZE

        block_is_below = ((isinstance(part_below_1, Part) and part_below_1.pt in BLOCK_PARTS) or
                          (isinstance(part_below_2, Part) and part_below_2.pt in BLOCK_PARTS)) and \
                         self.player_jump_velocity >= 0 and \
                         player_padding_below >= bounder_line_below

        if block_is_below:
            self.player_jump_velocity = 0
            self.player_position[1] = math.ceil(self.player_position[1])

        # apply gravity
        else:
            self.player_position[1] += self.player_jump_velocity * dt + 0.5 * self.GRAVITY * dt ** 2
            self.player_jump_velocity += self.GRAVITY * dt

        # block besides the player.
        part_from_right0 = all_parts.get((math.ceil(self.player_position[0]), math.ceil(self.player_position[1])))
        part_from_left0 = all_parts.get((math.floor(self.player_position[0]), math.ceil(self.player_position[1])))
        part_from_right1 = all_parts.get((math.ceil(self.player_position[0]), math.ceil(self.player_position[1] - 1)))
        part_from_left1 = all_parts.get((math.floor(self.player_position[0]), math.ceil(self.player_position[1] - 1)))

        player_padding_right = (self.player_position[0] + 1) * BLOCK_SIZE + 10
        player_padding_left = (self.player_position[0]) * BLOCK_SIZE + 10
        bounder_line_right = (math.ceil(self.player_position[0])) * BLOCK_SIZE
        bounder_line_left = (math.floor(self.player_position[0])) * BLOCK_SIZE

        block_on_right0 = isinstance(part_from_right0, Part) and part_from_right0.pt in BLOCK_PARTS and \
                          player_padding_right >= bounder_line_right
        block_on_left0 = isinstance(part_from_left0, Part) and part_from_left0.pt in BLOCK_PARTS and \
                         player_padding_left >= bounder_line_left
        block_on_right1 = isinstance(part_from_right1, Part) and part_from_right1.pt in BLOCK_PARTS and \
                          player_padding_right >= bounder_line_right
        block_on_left1 = isinstance(part_from_left1, Part) and part_from_left1.pt in BLOCK_PARTS and \
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

        block_from_above = ((isinstance(part_above0, Part) and part_above0.pt in BLOCK_PARTS) or
                            (isinstance(part_above1, Part) and part_above1.pt in BLOCK_PARTS)) and \
                           self.player_jump_velocity <= 0 and \
                           above_player_padding <= above_player_part

        if block_from_above:
            self.player_stuck[2] = True
            self.player_jump_velocity = 0
            self.player_position[1] = math.floor(self.player_position[1])

            # if isinstance(part_above0, Part) and part_above0.pt in BREAKABLE_BLOCKS:
            #     self._break_breakable(math.floor(self.player_position[0]),
            #                           math.floor(self.player_position[1] - 1))
            #
            # if isinstance(part_above1, Part) and part_above1.pt in BREAKABLE_BLOCKS:
            #     self._break_breakable(math.ceil(self.player_position[0]),
            #                           math.floor(self.player_position[1] - 1))

        else:
            self.player_stuck[2] = False

    def reset(self):
        self.player_position = [W_BLOCKS // 2, H_BLOCKS - 3]
        self.player_velocity = PLAYER_VELOCITY.get("normal")
        self.player_crouch = False
        self.player_stuck = [False, False, False]  # [from_left, from_right, from_top]
        self.player_direction = Direction.FRONT
        self.player_jump_height = PLAYER_JUMP_H.get("normal")
        self.player_jump_velocity = 0
        self.init_floor()
        self.map.map_0()

    def apply_game_rules(self):

        if self.player_position[1] > H_BLOCKS + 1:
            self.reset()

    def _throw_pizza(self):
        if not self.player_direction == Direction.FRONT:

            padding = 1  # throws the pizza one block away from the player
            if self.player_direction == Direction.LEFT:
                padding *= -1

            if not self.player_crouch:
                self.pizza_objects.append(Part(self.player_position[0] + padding,
                                               math.floor(self.player_position[1] - 1),
                                               PT.PIZZA, pygame.time.get_ticks() + self.pizza_lifetime,
                                               self.player_direction))
            else:
                self.pizza_objects.append(Part(self.player_position[0] + padding,
                                               math.floor(self.player_position[1]),
                                               PT.MINI_PIZZA, pygame.time.get_ticks() + self.pizza_lifetime,
                                               self.player_direction))


class Maps:
    def __init__(self, game: Game):
        self.maps = []
        self.game = game

    @staticmethod
    def _stairs_right(start_pos: tuple[int, int], pt: PT, amount: int, length: int) -> int:
        for i in range(amount):
            for j in range(i + 1):
                for k in range(length):
                    Part(start_pos[0] + i * length + k, start_pos[1] - j, pt)
        return amount * length

    @staticmethod
    def _stairs_left(start_pos: tuple[int, int], pt: PT, amount: int, length: int) -> int:
        start_pos0 = start_pos[0] + amount * length -1
        for i in range(amount):
            for j in range(i + 1):
                for k in range(length):
                    Part(start_pos0 - i * length - k, start_pos[1] - j, pt)
        return amount * length

    @staticmethod
    def _hill(start_pos: tuple[int, int], pt: PT, height: int, length: int) -> int:

        stair_height = math.ceil(height / (2.0*length))
        stair_length = math.ceil(length / (2.0*stair_height))
        print((stair_height, stair_length))
        x_0 = start_pos[0]
        x_0 += Maps._stairs_right((x_0, start_pos[1]), pt, length//2, stair_length)
        x_0 += Maps._stairs_left((x_0, start_pos[1]), pt, length//2, stair_length)
        return length

    def map_0(self):
        level_0 = H_BLOCKS - 3
        x_0 = W_BLOCKS // 2

        self.game.player_position[1] = level_0 - 2

        for i in range(4):
            Part(x_0 - 2 + i, level_0 - 1, PT.BOX)
            Part(x_0 - 2 + i, level_0, PT.BOX)

        self._hill((x_0 + 6, level_0), PT.BRICK, 50, 10)
        self._hill((x_0 + 18, level_0), PT.BRICK, 60, 20)


def main():
    game = Game(WIDTH, HEIGHT)

    while game.running:
        dt = game.clock.tick(60) / 1000

        game.screen.fill(PART_COLOR.get("background"))

        game.init_floor()
        game.draw_parts()
        game.apply_game_rules()
        game.handle_keys(dt)
        game.update_player_position(dt)
        game.update_pizzas_position(dt)
        game.draw_player()
        pygame.display.flip()


if __name__ == "__main__":
    main()
