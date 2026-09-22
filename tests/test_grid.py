import random

import pytest

from pyconway import Grid, proof_of_life


@pytest.mark.parametrize(
    ("alive", "neighbors", "expected"),
    [
        (False, 2, False),
        (False, 3, True),
        (False, 4, False),
        (True, 1, False),
        (True, 2, True),
        (True, 3, True),
        (True, 4, False),
    ],
)
def test_proof_of_life(alive: bool, neighbors: int, expected: bool) -> None:
    assert proof_of_life(alive, neighbors) is expected


def empty_grid(width: int = 5, height: int = 5, *, wrap: bool = False) -> Grid:
    grid = Grid(width, height, wrap=wrap)
    grid.cells = [[False] * width for _ in range(height)]
    grid.history.clear()
    return grid


def test_block_is_still_life() -> None:
    grid = empty_grid()
    for x, y in ((1, 1), (2, 1), (1, 2), (2, 2)):
        grid.cells[y][x] = True

    before = [row[:] for row in grid.cells]
    grid.step()

    assert grid.cells == before


def test_blinker_oscillates() -> None:
    grid = empty_grid()
    for x, y in ((2, 1), (2, 2), (2, 3)):
        grid.cells[y][x] = True

    grid.step()

    assert grid.cells[2] == [False, True, True, True, False]


def test_step_back_restores_previous_generation() -> None:
    grid = empty_grid()
    grid.cells[2][1:4] = [True, True, True]
    before = [row[:] for row in grid.cells]

    grid.step()

    assert grid.step_back() is True
    assert grid.cells == before
    assert grid.step_back() is False


def test_wrapping_connects_opposite_edges() -> None:
    grid = empty_grid(wrap=True)
    for x, y in ((4, 4), (0, 4), (4, 0)):
        grid.cells[y][x] = True

    grid.step()

    assert grid.cells[0][0] is True


def test_seeded_grids_are_reproducible() -> None:
    first = Grid(5, 5, rng=random.Random(42))
    second = Grid(5, 5, rng=random.Random(42))

    assert first.cells == second.cells


def test_resize_preserves_top_left_and_clears_history() -> None:
    grid = empty_grid()
    grid.cells[1][1] = True
    grid.step()

    assert grid.resize(3, 3) is True
    assert grid.cells[1][1] is False
    assert not grid.history


@pytest.mark.parametrize(("width", "height"), [(0, 1), (1, 0), (-1, 1)])
def test_dimensions_must_be_positive(width: int, height: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        Grid(width, height)
