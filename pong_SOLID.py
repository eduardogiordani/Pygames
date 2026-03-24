import sys
import math
import array
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pygame


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

    BOUNCE_ANGLE_VARIANCE: float = 0.35
    BALL_MIN_VY:           float = 1.5
    BALL_MAX_SPEED:        float = 14.0

    POWERUP_INTERVAL_MS:   int   = 5000
    POWERUP_BALL_COUNT:    int   = 3

    AUDIO_FREQ:     int   = 44100
    AUDIO_CHANNELS: int   = 2
    AUDIO_BUFFER:   int   = 512
    MUSIC_VOLUME:   float = 0.25
    SFX_VOLUME:     float = 0.7

    BLACK: tuple = field(default=(0,   0,   0))
    WHITE: tuple = field(default=(255, 255, 255))


class Drawable(ABC):
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...


class PhysicsEngine:
    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def bounce_off_wall(self, ball: "Ball") -> None:
        ball.vy = -ball.vy
        ball.vy += random.uniform(-self._s.BOUNCE_ANGLE_VARIANCE,
                                   self._s.BOUNCE_ANGLE_VARIANCE)
        self._enforce_min_vy(ball)
        self._clamp_speed(ball)

    def bounce_off_paddle(self, ball: "Ball", paddle: "Paddle") -> None:
        ball.vx = -ball.vx
        offset   = (ball.y - (paddle.y + self._s.PADDLE_HEIGHT / 2)) / (self._s.PADDLE_HEIGHT / 2)
        ball.vy += offset * self._s.BOUNCE_ANGLE_VARIANCE * 2
        ball.vy += random.uniform(-self._s.BOUNCE_ANGLE_VARIANCE,
                                   self._s.BOUNCE_ANGLE_VARIANCE)
        self._enforce_min_vy(ball)
        self._clamp_speed(ball)

    def _enforce_min_vy(self, ball: "Ball") -> None:
        if abs(ball.vy) < self._s.BALL_MIN_VY:
            ball.vy = math.copysign(self._s.BALL_MIN_VY, ball.vy)

    def _clamp_speed(self, ball: "Ball") -> None:
        speed = math.hypot(ball.vx, ball.vy)
        if speed > self._s.BALL_MAX_SPEED:
            scale   = self._s.BALL_MAX_SPEED / speed
            ball.vx *= scale
            ball.vy *= scale


class SoundManager:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        pygame.mixer.init(
            frequency=settings.AUDIO_FREQ,
            size=-16,
            channels=settings.AUDIO_CHANNELS,
            buffer=settings.AUDIO_BUFFER,
        )
        self._paddle_sound = self._make_beep(frequency=480, duration_ms=40, wave="square")
        self._wall_sound   = self._make_beep(frequency=220, duration_ms=35, wave="square")
        self._score_sound  = self._make_score_jingle()
        self._music        = self._make_music_loop()

        self._paddle_sound.set_volume(settings.SFX_VOLUME)
        self._wall_sound.set_volume(settings.SFX_VOLUME)
        self._score_sound.set_volume(settings.SFX_VOLUME)

    def play_paddle_hit(self) -> None:
        self._paddle_sound.play()

    def play_wall_hit(self) -> None:
        self._wall_sound.play()

    def play_score(self) -> None:
        self._score_sound.play()

    def start_music(self) -> None:
        self._music.set_volume(self._s.MUSIC_VOLUME)
        self._music.play(loops=-1)

    def stop_music(self) -> None:
        self._music.stop()

    def _make_beep(self, frequency: float, duration_ms: int,
                   wave: str = "sine") -> pygame.mixer.Sound:
        n_samples = int(self._s.AUDIO_FREQ * duration_ms / 1000)
        buf = array.array("h", [0] * (n_samples * self._s.AUDIO_CHANNELS))
        amp = 32767 * 0.6

        for i in range(n_samples):
            t     = i / self._s.AUDIO_FREQ
            phase = 2 * math.pi * frequency * t

            if wave == "square":
                raw = amp if math.sin(phase) >= 0 else -amp
            elif wave == "sawtooth":
                raw = amp * (2 * ((frequency * t) % 1) - 1)
            else:
                raw = amp * math.sin(phase)

            envelope = max(0.0, 1.0 - i / n_samples)
            sample   = int(raw * envelope)

            if self._s.AUDIO_CHANNELS == 2:
                buf[i * 2]     = sample
                buf[i * 2 + 1] = sample
            else:
                buf[i] = sample

        return pygame.mixer.Sound(buffer=buf)

    def _make_score_jingle(self) -> pygame.mixer.Sound:
        notes  = [330, 440, 550]
        dur_ms = 100
        n_note = int(self._s.AUDIO_FREQ * dur_ms / 1000)
        total  = n_note * len(notes)
        buf    = array.array("h", [0] * (total * self._s.AUDIO_CHANNELS))
        amp    = 32767 * 0.55

        for note_idx, freq in enumerate(notes):
            offset = note_idx * n_note
            for i in range(n_note):
                t        = i / self._s.AUDIO_FREQ
                envelope = max(0.0, 1.0 - i / n_note)
                sample   = int(amp * math.sin(2 * math.pi * freq * t) * envelope)
                pos      = (offset + i) * self._s.AUDIO_CHANNELS
                if self._s.AUDIO_CHANNELS == 2:
                    buf[pos]     = sample
                    buf[pos + 1] = sample
                else:
                    buf[pos] = sample

        return pygame.mixer.Sound(buffer=buf)

    def _make_music_loop(self) -> pygame.mixer.Sound:
        duration_s = 2.0
        n_samples  = int(self._s.AUDIO_FREQ * duration_s)
        buf        = array.array("h", [0] * (n_samples * self._s.AUDIO_CHANNELS))
        amp        = 32767 * 0.18
        bass_notes = [55, 69, 82, 110]
        note_dur   = int(n_samples / len(bass_notes))

        for note_idx, freq in enumerate(bass_notes):
            start = note_idx * note_dur
            end   = start + note_dur
            for i in range(start, min(end, n_samples)):
                t      = i / self._s.AUDIO_FREQ
                val    = amp if math.sin(2 * math.pi * freq * t) >= 0 else -amp
                local  = i - start
                env    = min(1.0, local / (note_dur * 0.05))
                sample = int(val * env)
                pos    = i * self._s.AUDIO_CHANNELS
                if self._s.AUDIO_CHANNELS == 2:
                    buf[pos]     = sample
                    buf[pos + 1] = sample
                else:
                    buf[pos] = sample

        return pygame.mixer.Sound(buffer=buf)


class Ball(Drawable):
    def __init__(self, settings: Settings,
                 is_real: bool = True,
                 color: tuple = None) -> None:
        self._s      = settings
        self.is_real = is_real
        self.color   = color if color is not None else settings.WHITE
        self.reset()

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self._s.BALL_SIZE, self._s.BALL_SIZE)

    def reset(self) -> None:
        self.x: float  = (self._s.SCREEN_WIDTH  - self._s.BALL_SIZE) / 2
        self.y: float  = (self._s.SCREEN_HEIGHT - self._s.BALL_SIZE) / 2
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

    def is_out_of_bounds(self) -> bool:
        return self.x <= 0 or self.x >= self._s.SCREEN_WIDTH - self._s.BALL_SIZE

    def hits_top_or_bottom(self) -> bool:
        return self.y <= 0 or self.y >= self._s.SCREEN_HEIGHT - self._s.BALL_SIZE

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface, self.color,
            (int(self.x), int(self.y)), self._s.BALL_SIZE,
        )


class Paddle(Drawable, ABC):
    def __init__(self, x: int, settings: Settings) -> None:
        self._s = settings
        self.x  = x
        self.y: float = (settings.SCREEN_HEIGHT - settings.PADDLE_HEIGHT) / 2

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x, int(self.y),
            self._s.PADDLE_WIDTH, self._s.PADDLE_HEIGHT,
        )

    @abstractmethod
    def update(self, ball: Ball) -> None: ...

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

    def update(self, ball: Ball) -> None:
        keys = pygame.key.get_pressed()
        if keys[self._key_up]   and self.y > 0:
            self.y -= self._s.PADDLE_SPEED
        if keys[self._key_down] and self.y < self._s.SCREEN_HEIGHT - self._s.PADDLE_HEIGHT:
            self.y += self._s.PADDLE_SPEED
        self._clamp()


class AIPaddle(Paddle):
    def update(self, ball: Ball) -> None:
        center = self.y + self._s.PADDLE_HEIGHT / 2
        if center < ball.y:
            self.y += self._s.AI_SPEED
        elif center > ball.y:
            self.y -= self._s.AI_SPEED
        self._clamp()


class PowerUpManager:
    def __init__(self, settings: Settings) -> None:
        self._s              = settings
        self._last_powerup   = pygame.time.get_ticks()
        self._powerup_ready  = False

    def tick(self) -> None:
        elapsed = pygame.time.get_ticks() - self._last_powerup
        if elapsed >= self._s.POWERUP_INTERVAL_MS:
            self._powerup_ready = True

    def should_fragment(self) -> bool:
        return self._powerup_ready

    def spawn_fragments(self, origin: Ball) -> list:
        self._powerup_ready  = False
        self._last_powerup   = pygame.time.get_ticks()

        fragments = []
        for _ in range(self._s.POWERUP_BALL_COUNT):
            color = (
                random.randint(80, 255),
                random.randint(80, 255),
                random.randint(80, 255),
            )
            fake       = Ball(self._s, is_real=False, color=color)
            fake.x     = origin.x
            fake.y     = origin.y
            fake.vx    = origin.vx * random.uniform(0.8, 1.2) * random.choice([-1, 1])
            fake.vy    = origin.vy * random.uniform(0.8, 1.2) * random.choice([-1, 1])
            fragments.append(fake)

        return fragments

    def reset(self) -> None:
        self._last_powerup  = pygame.time.get_ticks()
        self._powerup_ready = False


class Scoreboard(Drawable):
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self.score_p1 = 0
        self.score_p2 = 0
        self._font = pygame.font.SysFont(None, 36)

    def point_to_p1(self) -> None: self.score_p1 += 1
    def point_to_p2(self) -> None: self.score_p2 += 1
    def p1_wins(self) -> bool: return self.score_p1 >= self._s.WINNING_SCORE
    def p2_wins(self) -> bool: return self.score_p2 >= self._s.WINNING_SCORE

    def draw(self, surface: pygame.Surface) -> None:
        text = self._font.render(
            f"{self.score_p1} - {self.score_p2}", True, self._s.WHITE
        )
        surface.blit(text, text.get_rect(center=(self._s.SCREEN_WIDTH // 2, 30)))


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
            text.get_rect(center=(self._s.SCREEN_WIDTH  // 2,
                                  self._s.SCREEN_HEIGHT // 4 + 50)),
        )

    def _draw_blinking_prompt(self) -> None:
        if pygame.time.get_ticks() % 2000 < 1000:
            text = self._subtitle.render(
                "Pressione ESPAÇO para jogar", True, self._s.WHITE
            )
            self._surface.blit(
                text,
                text.get_rect(center=(self._s.SCREEN_WIDTH  // 2,
                                      self._s.SCREEN_HEIGHT // 2 + 60)),
            )


class GameScene:
    def __init__(self, surface: pygame.Surface,
                 settings: Settings,
                 sound: SoundManager,
                 physics: PhysicsEngine,
                 powerup: PowerUpManager) -> None:
        self._surface = surface
        self._s       = settings
        self._sound   = sound
        self._physics = physics
        self._powerup = powerup
        self._clock   = pygame.time.Clock()
        self._board   = Scoreboard(settings)

        self._p1: Paddle = HumanPaddle(
            x=15, settings=settings,
            key_up=pygame.K_UP, key_down=pygame.K_DOWN,
        )
        self._p2: Paddle = AIPaddle(
            x=settings.SCREEN_WIDTH - 15 - settings.PADDLE_WIDTH,
            settings=settings,
        )

        self._real_ball: Ball    = Ball(settings, is_real=True, color=settings.WHITE)
        self._balls: list[Ball]  = [self._real_ball]

    def run(self) -> bool:
        self._sound.start_music()
        try:
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
        finally:
            self._sound.stop_music()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

    def _update(self) -> None:
        self._powerup.tick()
        self._p1.update(self._real_ball)
        self._p2.update(self._real_ball)

        for ball in self._balls:
            ball.move()

        self._check_collisions()
        self._discard_fake_balls()

    def _check_collisions(self) -> None:
        new_fragments: list[Ball] = []

        for ball in self._balls:
            if ball.hits_top_or_bottom():
                self._physics.bounce_off_wall(ball)
                self._sound.play_wall_hit()

            hit_paddle = None
            if ball.rect.colliderect(self._p1.rect):
                hit_paddle = self._p1
            elif ball.rect.colliderect(self._p2.rect):
                hit_paddle = self._p2

            if hit_paddle is not None:
                self._physics.bounce_off_paddle(ball, hit_paddle)
                self._sound.play_paddle_hit()

                if ball.is_real and self._powerup.should_fragment():
                    new_fragments = self._powerup.spawn_fragments(ball)

            if ball.is_real:
                if ball.is_out_left():
                    self._board.point_to_p2()
                    print(f"Player 2: {self._board.score_p2}")
                    self._sound.play_score()
                    self._reset_round()
                    return
                elif ball.is_out_right():
                    self._board.point_to_p1()
                    print(f"Player 1: {self._board.score_p1}")
                    self._sound.play_score()
                    self._reset_round()
                    return

        self._balls.extend(new_fragments)

    def _discard_fake_balls(self) -> None:
        self._balls = [b for b in self._balls if b.is_real or not b.is_out_of_bounds()]

    def _reset_round(self) -> None:
        self._real_ball.reset()
        self._balls = [self._real_ball]
        self._powerup.reset()

    def _render(self) -> None:
        self._surface.fill(self._s.BLACK)
        self._p1.draw(self._surface)
        self._p2.draw(self._surface)
        for ball in self._balls:
            ball.draw(self._surface)
        self._board.draw(self._surface)
        pygame.display.flip()


def main() -> None:
    pygame.init()
    settings = Settings()
    surface  = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption("Pong")

    sound   = SoundManager(settings)
    physics = PhysicsEngine(settings)
    powerup = PowerUpManager(settings)
    menu    = MenuScene(surface, settings)
    game    = GameScene(surface, settings, sound, physics, powerup)

    while True:
        if not menu.run():
            break
        if not game.run():
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()