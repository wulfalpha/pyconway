import argparse
import os
import random
import sys
from collections import deque
from typing import ClassVar, NamedTuple, cast, override

from textual import events
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.geometry import Size
from textual.reactive import reactive
from textual.theme import BUILTIN_THEMES
from textual.widgets import Footer, Static

HISTORY_LIMIT = 200
THEME_ENV_VAR = "CONWAY_THEME"


def proof_of_life(status: bool, neighbors: int) -> bool:
    if status:
        return neighbors in (2, 3)

    return neighbors == 3


class Grid:
    def __init__(
        self,
        width: int,
        height: int,
        *,
        wrap: bool = False,
        rng: random.Random | None = None,
        history_limit: int = HISTORY_LIMIT,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")

        if wrap and (width < 3 or height < 3):
            raise ValueError("Wrapped grids must be at least 3×3")

        self.width: int = width
        self.height: int = height
        self.wrap: bool = wrap
        self.rng: random.Random = rng if rng is not None else random.Random()

        self.cells: list[list[bool]] = [
            [self.rng.choice((True, False)) for _ in range(width)]
            for _ in range(height)
        ]
        self.history: deque[list[list[bool]]] = deque(maxlen=history_limit)

    def count_neighbors(self, x: int, y: int) -> int:
        count = 0

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue

                nx = x + dx
                ny = y + dy

                if self.wrap:
                    nx %= self.width
                    ny %= self.height
                elif not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                if self.cells[ny][nx]:
                    count += 1

        return count

    def step(self) -> None:
        self.history.append([row[:] for row in self.cells])

        self.cells = [
            [
                proof_of_life(
                    self.cells[y][x],
                    self.count_neighbors(x, y),
                )
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

    def step_back(self) -> bool:
        if not self.history:
            return False

        self.cells = self.history.pop()
        return True

    def resize(self, width: int, height: int) -> bool:
        if width == self.width and height == self.height:
            return False

        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")

        if self.wrap and (width < 3 or height < 3):
            raise ValueError("Wrapped grids must be at least 3×3")

        new_cells = [[False] * width for _ in range(height)]

        for y in range(min(height, self.height)):
            for x in range(min(width, self.width)):
                new_cells[y][x] = self.cells[y][x]

        self.width = width
        self.height = height
        self.cells = new_cells
        self.history.clear()

        return True

    def randomize(self) -> None:
        self.cells = [
            [self.rng.choice((True, False)) for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.history.clear()

    def render(self) -> str:
        return "\n".join(
            "".join("██" if is_alive else "  " for is_alive in row)
            for row in self.cells
        )


class ConwayApp(App[None]):
    CSS: ClassVar[str] = """
    #top-bar {
        height: 1;
        width: 100%;
        text-align: center;
        text-style: bold;
    }

    #board {
        height: 1fr;
        width: 100%;
        overflow: hidden;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "Quit"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("l,right", "step", "Step"),
        ("h,left", "step_back", "Step Back"),
        ("r", "randomize", "Randomize"),
        ("w", "toggle_wrap", "Toggle Wrap"),
    ]

    paused: reactive[bool] = reactive(False)

    def __init__(
        self,
        width: int | None = None,
        height: int | None = None,
        *,
        wrap: bool = False,
        seed: int | None = None,
        crypto: bool = False,
        theme: str | None = None,
    ) -> None:
        super().__init__()

        self.requested_width: int | None = width
        self.requested_height: int | None = height
        self.initial_wrap: bool = wrap
        self.seed: int | None = seed
        self.crypto: bool = crypto
        self.initial_theme: str | None = theme

        self.generation: int = 0
        self.grid: Grid = Grid(1, 1)

        self.top_bar: Static = Static(id="top-bar")
        self.board: Static = Static(id="board")

    @override
    def compose(self) -> ComposeResult:
        yield self.top_bar
        yield self.board
        yield Footer()

    def _compute_dimensions(self, size: Size) -> tuple[int, int]:
        width = (
            self.requested_width
            if self.requested_width is not None
            else max(1, size.width // 2)
        )

        height = (
            self.requested_height
            if self.requested_height is not None
            else max(1, size.height - 1)
        )

        return width, height

    def on_mount(self) -> None:
        if self.initial_theme is not None:
            self.theme = self.initial_theme

        width, height = self._compute_dimensions(self.size)

        rng = random.SystemRandom() if self.crypto else random.Random(self.seed)

        self.grid = Grid(
            width,
            height,
            wrap=self.initial_wrap,
            rng=rng,
        )

        self.update_display()
        self.set_interval(0.1, self.tick)

    def on_resize(self, event: events.Resize) -> None:
        width, height = self._compute_dimensions(event.size)

        if self.grid.resize(width, height):
            self.update_display()

    def update_display(self) -> None:
        self.top_bar.update(f"Generation: {self.generation}")
        self.board.update(self.grid.render())

    def tick(self) -> None:
        if self.paused:
            return

        self.grid.step()
        self.generation += 1
        self.update_display()

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused

    def action_step(self) -> None:
        self.paused = True
        self.grid.step()
        self.generation += 1
        self.update_display()

    def action_step_back(self) -> None:
        self.paused = True

        if not self.grid.step_back():
            self.notify("No earlier generation to step back to", severity="warning")
            return

        self.generation -= 1
        self.update_display()

    def action_randomize(self) -> None:
        self.grid.randomize()
        self.generation = 0
        self.update_display()

    def action_toggle_wrap(self) -> None:
        if not self.grid.wrap and (self.grid.width < 3 or self.grid.height < 3):
            self.notify(
                "Wraparound requires a grid of at least 3×3",
                severity="warning",
            )
            return

        self.grid.wrap = not self.grid.wrap

        boundary_name = "wraparound" if self.grid.wrap else "dead"
        self.notify(f"Boundary mode: {boundary_name}")


class CliArgs(NamedTuple):
    width: int | None
    height: int | None
    wrap: bool
    seed: int | None
    crypto: bool
    theme: str | None


def parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(
        description="Conway's Game of Life",
    )

    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="grid width in cells; defaults to half the terminal columns",
    )

    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="grid height in cells; defaults to terminal rows minus the top bar",
    )

    parser.add_argument(
        "--wrap",
        action="store_true",
        help="start with wraparound boundaries enabled",
    )

    rng_group = parser.add_mutually_exclusive_group()

    rng_group.add_argument(
        "--seed",
        type=int,
        default=None,
        help="seed the PRNG for a reproducible initial board",
    )

    rng_group.add_argument(
        "-c",
        "--crypto",
        action="store_true",
        help=(
            "use a cryptographically secure, unseedable RNG for the initial "
            "board (mutually exclusive with --seed)"
        ),
    )

    parser.add_argument(
        "--theme",
        type=str,
        default=None,
        choices=sorted(BUILTIN_THEMES),
        help=(
            "Textual theme to start with; falls back to the "
            f"{THEME_ENV_VAR} environment variable, then Textual's default"
        ),
    )

    args = parser.parse_args()

    width = cast("int | None", args.width)
    height = cast("int | None", args.height)
    wrap = cast("bool", args.wrap)
    seed = cast("int | None", args.seed)
    crypto = cast("bool", args.crypto)
    theme = cast("str | None", args.theme) or resolve_env_theme()

    return CliArgs(
        width=width, height=height, wrap=wrap, seed=seed, crypto=crypto, theme=theme
    )


def resolve_env_theme() -> str | None:
    theme = os.environ.get(THEME_ENV_VAR)

    if theme is None:
        return None

    if theme not in BUILTIN_THEMES:
        choices = ", ".join(sorted(BUILTIN_THEMES))
        message = f"warning: ignoring unknown {THEME_ENV_VAR}={theme!r} (choose from: {choices})"
        print(message, file=sys.stderr)
        return None

    return theme


def main() -> None:
    cli = parse_args()

    ConwayApp(
        width=cli.width,
        height=cli.height,
        wrap=cli.wrap,
        seed=cli.seed,
        crypto=cli.crypto,
        theme=cli.theme,
    ).run()


if __name__ == "__main__":
    main()
