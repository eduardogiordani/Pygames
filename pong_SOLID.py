import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pygame


# ──────────────────────────────────────────────
# Configurações centralizadas
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class Settings:
    SCREEN_WIDTH:  int   = 800
    SCREEN_HEIGHT: int   = 600
    FPS:           int   = 60
    WINNING_SCORE: int   = 10

    PADDLE_WIDTH:  int   = 10
    PADDLE_HEIGHT: int   = 80
    PADDLE_SPEED:  int   = 5

    BALL_SIZE:     int   = 7
    BALL_SPEED_X:  float = 8.0
    BALL_SPEED_Y:  float = 8.0
    AI_SPEED:      int   = 5

    BLACK: tuple = field(default=(0, 0, 0))
    WHITE: tuple = field(default=(255, 255, 255))

# ──────────────────────────────────────────────
# Interface
# ──────────────────────────────────────────────

class Drawable(ABC):

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...

# ──────────────────────────────────────────────
# Entidades de domínio
# ──────────────────────────────────────────────

class Ball(Drawable):

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self.reset()

    # ── estado público ──────────────────────────
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self._s.BALL_SIZE, self._s.BALL_SIZE)

    # ── comportamento ───────────────────────────
    def reset(self) -> None:
        self.x: float = (self._s.SCREEN_WIDTH  - self._s.BALL_SIZE) / 2
        self.y: float = (self._s.SCREEN_HEIGHT - self._s.BALL_SIZE) / 2
        self.vx: float = self._s.BALL_SPEED_X
        self.vy: float = self._s.BALL_SPEED_Y

    def move(self) -> None:
        self.x += self.vx
        self.y += self.vy

    def bounce_vertical(self) -> None:
        self.vy = -self.vy

    def bounce_horizontal(self) -> None:
        self.vx = -self.vx

    def is_out_left(self) -> bool:
        return self.x <= 0

    def is_out_right(self) -> bool:
        return self.x >= self._s.SCREEN_WIDTH - self._s.BALL_SIZE

    def hits_top_or_bottom(self) -> bool:
        return self.y <= 0 or self.y >= self._s.SCREEN_HEIGHT - self._s.BALL_SIZE

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            self._s.WHITE,
            (int(self.x), int(self.y)),
            self._s.BALL_SIZE,
        )


class Paddle(Drawable, ABC):


    def __init__(self, x: int, settings: Settings) -> None:
        self._s = settings
        self.x = x
        self.y: float = (settings.SCREEN_HEIGHT - settings.PADDLE_HEIGHT) / 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x, int(self.y),
            self._s.PADDLE_WIDTH, self._s.PADDLE_HEIGHT,
        )

    @abstractmethod
    def update(self, ball: Ball) -> None:
        ...

    def _clamp(self) -> None:
        self.y = max(0.0, min(self.y, self._s.SCREEN_HEIGHT - self._s.PADDLE_HEIGHT))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self._s.WHITE, self.rect)


class HumanPaddle(Paddle):

    def __init__(self, x: int, settings: Settings,
                 key_up: int, key_down: int) -> None:
        super().__init__(x, settings)
        self._key_up   = key_up
        self._key_down = key_down

    def update(self, ball: Ball) -> None:  # bola ignorado para jogador humano
        keys = pygame.key.get_pressed()
        if keys[self._key_up]   and self.y > 0:
            self.y -= self._s.PADDLE_SPEED
        if keys[self._key_down] and self.y < self._s.SCREEN_HEIGHT - self._s.PADDLE_HEIGHT:
            self.y += self._s.PADDLE_SPEED
        self._clamp()


class AIPaddle(Paddle):

    def update(self, ball: Ball) -> None:
        paddle_center = self.y + self._s.PADDLE_HEIGHT / 2
        if paddle_center < ball.y:
            self.y += self._s.AI_SPEED
        elif paddle_center > ball.y:
            self.y -= self._s.AI_SPEED
        self._clamp()


# ──────────────────────────────────────────────
# Placar
# ──────────────────────────────────────────────

class Scoreboard(Drawable):


    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self.score_p1 = 0
        self.score_p2 = 0
        self._font = pygame.font.SysFont(None, 36)

    def point_to_p1(self) -> None:
        self.score_p1 += 1

    def point_to_p2(self) -> None:
        self.score_p2 += 1

    def p1_wins(self) -> bool:
        return self.score_p1 >= self._s.WINNING_SCORE

    def p2_wins(self) -> bool:
        return self.score_p2 >= self._s.WINNING_SCORE

    def draw(self, surface: pygame.Surface) -> None:
        text = self._font.render(
            f"{self.score_p1} - {self.score_p2}", True, self._s.WHITE
        )
        surface.blit(text, text.get_rect(center=(self._s.SCREEN_WIDTH // 2, 30)))

# ──────────────────────────────────────────────
# Telas / cenas
# ──────────────────────────────────────────────

class MenuScene:


    def __init__(self, surface: pygame.Surface, settings: Settings) -> None:
        self._surface  = surface
        self._s        = settings
        self._title    = pygame.font.SysFont(None, 50)
        self._subtitle = pygame.font.SysFont(None, 26)

    def run(self) -> bool:

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    return True

            self._surface.fill(self._s.BLACK)
            self._draw_title()
            self._draw_blinking_prompt()
            pygame.display.flip()

    def _draw_title(self) -> None:
        text = self._title.render("Pong", True, self._s.WHITE)
        self._surface.blit(
            text,
            text.get_rect(center=(self._s.SCREEN_WIDTH // 2,
                                  self._s.SCREEN_HEIGHT // 4 + 50)),
        )

    def _draw_blinking_prompt(self) -> None:
        if pygame.time.get_ticks() % 2000 < 1000:
            text = self._subtitle.render(
                "Pressione ESPAÇO para jogar", True, self._s.WHITE
            )
            self._surface.blit(
                text,
                text.get_rect(center=(self._s.SCREEN_WIDTH // 2,
                                      self._s.SCREEN_HEIGHT // 2 + 60)),
            )

# ──────────────────────────────────────────────
# Lógica de jogo
# ──────────────────────────────────────────────

class GameScene:

    def __init__(self, surface: pygame.Surface, settings: Settings) -> None:
        self._surface = surface
        self._s       = settings
        self._clock   = pygame.time.Clock()

        self._ball  = Ball(settings)
        self._board = Scoreboard(settings)

        self._p1: Paddle = HumanPaddle(
            x=15, settings=settings,
            key_up=pygame.K_UP, key_down=pygame.K_DOWN,
        )
        self._p2: Paddle = AIPaddle(
            x=settings.SCREEN_WIDTH - 15 - settings.PADDLE_WIDTH,
            settings=settings,
        )
        self._drawables: list[Drawable] = [self._p1, self._p2, self._ball, self._board]

    def run(self) -> bool:

        while True:
            if self._handle_events() is False:
                return False

            self._update()
            self._render()

            if self._board.p1_wins():
                print("Player 1 venceu!")
                return True
            if self._board.p2_wins():
                print("Player 2 venceu!")
                return True

            self._clock.tick(self._s.FPS)

    # ── privados ────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

    def _update(self) -> None:
        self._ball.move()
        self._p1.update(self._ball)
        self._p2.update(self._ball)
        self._check_collisions()

    def _check_collisions(self) -> None:
        if self._ball.hits_top_or_bottom():
            self._ball.bounce_vertical()

        if (self._ball.rect.colliderect(self._p1.rect) or
                self._ball.rect.colliderect(self._p2.rect)):
            self._ball.bounce_horizontal()

        if self._ball.is_out_left():
            self._board.point_to_p2()
            print(f"Player 2: {self._board.score_p2}")
            self._ball.reset()
            self._ball.bounce_horizontal()

        elif self._ball.is_out_right():
            self._board.point_to_p1()
            print(f"Player 1: {self._board.score_p1}")
            self._ball.reset()
            self._ball.bounce_horizontal()

    def _render(self) -> None:
        self._surface.fill(self._s.BLACK)
        for drawable in self._drawables:
            drawable.draw(self._surface)
        pygame.display.flip()


# ──────────────────────────────────────────────
# Ponto de entrada
# ──────────────────────────────────────────────

def main() -> None:
    pygame.init()
    settings = Settings()
    surface  = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption("Pong")

    menu = MenuScene(surface, settings)
    game = GameScene(surface, settings)

    while True:
        if not menu.run():
            break
        if not game.run():
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
