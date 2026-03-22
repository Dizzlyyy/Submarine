import pytest
from probe_api.components.grid_manager import GridManager


@pytest.fixture
def gm():
    return GridManager()


# --- Obstacle tests ---

def test_obstacle_2_3_is_blocked(gm):
    assert gm.is_obstacle(2, 3) is True

def test_obstacle_9_11_is_blocked(gm):
    assert gm.is_obstacle(9, 11) is True

def test_non_obstacle_cell_is_not_blocked(gm):
    assert gm.is_obstacle(0, 0) is False
    assert gm.is_obstacle(5, 5) is False


# --- Boundary edge tests ---

def test_boundary_x_min_valid(gm):
    assert gm.is_within_bounds(0, 10) is True

def test_boundary_x_max_valid(gm):
    assert gm.is_within_bounds(19, 10) is True

def test_boundary_y_min_valid(gm):
    assert gm.is_within_bounds(10, 0) is True

def test_boundary_y_max_valid(gm):
    assert gm.is_within_bounds(10, 19) is True

def test_boundary_x_below_min_invalid(gm):
    assert gm.is_within_bounds(-1, 10) is False

def test_boundary_x_above_max_invalid(gm):
    assert gm.is_within_bounds(20, 10) is False

def test_boundary_y_below_min_invalid(gm):
    assert gm.is_within_bounds(10, -1) is False

def test_boundary_y_above_max_invalid(gm):
    assert gm.is_within_bounds(10, 20) is False


# --- is_cell_valid tests ---

def test_is_cell_valid_obstacle_returns_false(gm):
    assert gm.is_cell_valid(2, 3) is False
    assert gm.is_cell_valid(9, 11) is False

def test_is_cell_valid_out_of_bounds_returns_false(gm):
    assert gm.is_cell_valid(-1, 0) is False
    assert gm.is_cell_valid(20, 0) is False
    assert gm.is_cell_valid(0, -1) is False
    assert gm.is_cell_valid(0, 20) is False

def test_is_cell_valid_empty_in_bounds_returns_true(gm):
    assert gm.is_cell_valid(0, 0) is True
    assert gm.is_cell_valid(19, 19) is True
    assert gm.is_cell_valid(5, 5) is True


# --- Property tests ---

from hypothesis import given, settings
import hypothesis.strategies as st

# Feature: Probe_API, Property 1: Grid bounds are exactly 20×20
@given(st.integers(), st.integers())
@settings(max_examples=100)
def test_is_within_bounds_property(x, y):
    """Validates: Requirements 0.1"""
    gm = GridManager()
    expected = 0 <= x < 20 and 0 <= y < 20
    assert gm.is_within_bounds(x, y) == expected
