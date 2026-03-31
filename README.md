# Sudoku Solver

A constraint-based Sudoku solver written in Python. It combines **constraint propagation** with **backtracking search** to solve standard 9×9 puzzles, including notoriously difficult ones, typically in well under a second.

## How It Works

The solver uses two complementary techniques:

1. **Constraint Propagation** — Whenever a cell is pinned down to a single value, that value is eliminated from every peer (same row, column, or 3×3 block). This cascading elimination often solves easy puzzles outright without any guessing.

2. **Backtracking Search with MRV** — When propagation alone isn't enough, the solver picks the most constrained unsolved cell (the one with the fewest remaining candidates), makes a guess, and recurses. If a contradiction is found, it backtracks and tries the next candidate.

## Project Structure

| File | Purpose |
|---|---|
| `game.py` | Board geometry, peer lookups, and domain initialization |
| `ai.py` | Core solver: propagation, backtracking, and SAT encoding/decoding |
| `main.py` | CLI test harness — runs puzzles, verifies solutions, enforces time limits |
| `problems/` | Text files containing batches of puzzle strings (one per line) |

## Usage

```bash
# solve a single easy puzzle (propagation is enough)
python main.py -t 0

# solve a single hard puzzle (requires search)
python main.py -t 1

# run all 50 easy puzzles
python main.py -t 2

# run all 50 hard puzzles
python main.py -t 3

# show the grid before and after solving
python main.py -t 1 -d
```

## SAT Solver Mode (Optional)

The project also includes a SAT-based approach: the puzzle is encoded as a CNF formula in DIMACS format, passed to [PicoSAT](http://fmv.jku.at/picosat/), and the satisfying assignment is decoded back into a solved grid. This demonstrates that even the hardest puzzles become trivial for modern SAT solvers.

PicoSAT was developed by **Armin Biere** at Johannes Kepler University.

```bash
# run in SAT mode (requires picosat binary in the project root)
python main.py -t 3 -e
```

## Key Concepts

- **CSP (Constraint Satisfaction Problem)** modeling
- **Arc consistency** via iterative propagation
- **MRV (Minimum Remaining Values)** heuristic for variable ordering
- **Propositional logic** encoding (CNF / DIMACS format)
- **SAT solving** as a general-purpose constraint engine
