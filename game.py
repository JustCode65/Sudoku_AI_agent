# game.py — board setup and helper utilities for the sudoku solver
# handles all the grid geometry, peer lookups, and domain initialization

BLOCK_SIZE = 3
GRID_SIZE = BLOCK_SIZE ** 2

# row/col indices: 0 through 8
grid_range = list(range(0, GRID_SIZE))

# valid numbers you can place in a cell: 1 through 9
valid_nums = list(range(1, GRID_SIZE + 1))

# every (row, col) coordinate on the board
all_cells = [(r, c) for r in grid_range for c in grid_range]

# build a lookup dict: for each cell, store all its "peers"
# (cells that share a row, column, or 3x3 block)
peer_map = {}
for cell in all_cells:
    r, c = cell

    # same row, different column + same column, different row
    peers = [(r, cc) for cc in grid_range if cc != c] + \
            [(rr, c) for rr in grid_range if rr != r]

    # figure out the top-left corner of this cell's 3x3 block
    block_r = (r // BLOCK_SIZE) * BLOCK_SIZE
    block_c = (c // BLOCK_SIZE) * BLOCK_SIZE

    # add block peers (skip duplicates and self)
    for dr in range(BLOCK_SIZE):
        for dc in range(BLOCK_SIZE):
            neighbor = (block_r + dr, block_c + dc)
            if neighbor != cell:
                peers.append(neighbor)

    peer_map[cell] = peers


def make_domains():
    """Give every cell the full set of candidates to start with."""
    return {cell: list(valid_nums) for cell in all_cells}


def apply_clues(domains, puzzle_str):
    """
    Read the flat puzzle string (81 chars, '.' = blank)
    and lock in any pre-filled cells.
    """
    for r, c in all_cells:
        ch = puzzle_str[r * GRID_SIZE + c]
        if ch != '.':
            domains[(r, c)] = [int(ch)]
