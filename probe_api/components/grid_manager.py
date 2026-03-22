from __future__ import annotations


class GridManager:
    GRID_SIZE: int = 20
    OBSTACLES: frozenset[tuple[int, int]] = frozenset({(2, 3), (9, 11)})

    def is_within_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE

    def is_obstacle(self, x: int, y: int) -> bool:
        return (x, y) in self.OBSTACLES

    def is_cell_valid(self, x: int, y: int) -> bool:
        return self.is_within_bounds(x, y) and not self.is_obstacle(x, y)
