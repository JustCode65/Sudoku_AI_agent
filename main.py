# main.py — test harness for the sudoku solver
# runs puzzles through the AI, checks solutions, reports pass/fail

from ai import AI
from game import grid_range, make_domains, apply_clues, all_cells, BLOCK_SIZE, GRID_SIZE
import time
import argparse
import multiprocessing
import os

# ---- CLI setup ----
parser = argparse.ArgumentParser(description='Sudoku Solver')
parser.add_argument('--test', '-t', dest="test", type=int, default=0,
    help='0: easy single puzzle; 1: hard single puzzle; 2: easy batch; 3: hard batch')
parser.add_argument('--display', '-d', dest="disp", type=bool, default=False,
    nargs='?', const=True, help='show puzzle and solution grids')
parser.add_argument('--extra', '-e', dest="ec", type=bool, default=False,
    nargs='?', const=True, help='use SAT solver mode')
args = parser.parse_args()

# status codes for the tester
OK, BAD, TOO_SLOW = 0, 1, 2


def needs_separator(idx):
    """Check if we should draw a block divider after this index."""
    return ((idx + 1) != GRID_SIZE) and ((idx + 1) % BLOCK_SIZE == 0)


def print_grid(domains):
    """Pretty-print the sudoku board."""
    for r in grid_range:
        for c in grid_range:
            vals = domains[(r, c)]
            print(vals[0] if len(vals) == 1 else '.', end='')
            if needs_separator(c):
                print(" | ", end='')
        print()
        if needs_separator(r):
            print("-" * (GRID_SIZE + 3 * (BLOCK_SIZE - 1)))


def is_valid_solution(solution, original):
    """
    Verify that every cell is filled, respects the original clues,
    and no row/col/block has duplicates.
    """
    for cell in all_cells:
        d = solution[cell]
        if len(d) != 1:
            return False
        if d[0] not in original[cell]:
            return False

    # check rows
    for r in grid_range:
        seen = []
        for c in grid_range:
            num = solution[(r, c)][0]
            if num in seen:
                return False
            seen.append(num)

    # check columns
    for c in grid_range:
        seen = []
        for r in grid_range:
            num = solution[(r, c)][0]
            if num in seen:
                return False
            seen.append(num)

    # check 3x3 blocks
    for br in range(BLOCK_SIZE):
        for bc in range(BLOCK_SIZE):
            top_r = br * BLOCK_SIZE
            top_c = bc * BLOCK_SIZE
            seen = []
            for dr in range(BLOCK_SIZE):
                for dc in range(BLOCK_SIZE):
                    num = solution[(top_r + dr, top_c + dc)][0]
                    if num in seen:
                        return False
                    seen.append(num)

    return True


def run_single(problem, timeout, show=False, sat_mode=False):
    """Run one puzzle in a separate process so we can enforce a time limit."""
    mgr = multiprocessing.Manager()
    shared = mgr.dict()
    proc = multiprocessing.Process(
        target=_solve_and_check, name="Solve",
        args=(shared, problem, show, sat_mode))
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        print("Timed out after {} seconds.".format(timeout))
        proc.terminate()
        proc.join()
        return TOO_SLOW

    return OK if shared["passed"] else BAD


CNF_TMPFILE = "temp.cnf"

def _solve_and_check(shared, problem, show, sat_mode):
    """Worker function — actually runs the solver and checks the answer."""
    solver = AI()
    orig = make_domains()
    apply_clues(orig, problem)

    if show:
        print("====Problem====")
        print_grid(orig)
        print()

    t0 = time.time()

    if not sat_mode:
        result = solver.solve(problem)
    else:
        # write CNF, shell out to picosat, parse result
        with open(CNF_TMPFILE, 'w') as f:
            f.write(solver.sat_encode(problem))
        stream = os.popen("./picosat {}".format(CNF_TMPFILE))
        raw_output = stream.read()
        if len(raw_output) == 0:
            print("ERROR: picosat not found or not installed.")
            result = None
        else:
            os.remove(CNF_TMPFILE)
            sat_vars = _parse_picosat_output(raw_output)
            result = solver.sat_decode(sat_vars)

    elapsed = time.time() - t0
    passed = False if result is None else is_valid_solution(result, orig)

    if show:
        if result is not None:
            print("====Solution===")
            print_grid(result)
        else:
            print("==No solution==")
        print()
        print("Time: {:.4f}s".format(elapsed))
        print("Result:", "PASSED" if passed else "FAILED")
        print()

    shared["passed"] = passed


def run_batch(filepath, timeout, max_timeouts, show=False, sat_mode=False):
    """Run a whole file of puzzles, one per line."""
    with open(filepath, 'r') as f:
        puzzles = [line.strip() for line in f.readlines()]

    total = len(puzzles)
    timeouts_so_far = 0

    for i, puzzle in enumerate(puzzles):
        print("Test {}/{}:".format(i + 1, total))
        status = run_single(puzzle, timeout, show=show, sat_mode=sat_mode)

        if status == OK:
            print("PASSED")
        elif status == BAD:
            print("FAILED; stopping.")
            return
        else:
            timeouts_so_far += 1
            print("TIMEOUT ({}/{} allowed)".format(timeouts_so_far, max_timeouts))
            if timeouts_so_far >= max_timeouts:
                print("Too many timeouts; stopping.")
                return
        print()

    print("All tests PASSED.")


def _parse_picosat_output(text):
    """Turn picosat's stdout into a dict of {var_number: True/False}."""
    assignments = {}
    for line in text.split("\n")[1:]:  # skip the first line (s SATISFIABLE etc.)
        tokens = line.split()[1:]  # drop the leading 'v'
        for tok in tokens:
            num = int(tok)
            if num > 0:
                assignments[num] = True
            elif num < 0:
                assignments[-num] = False
    return assignments


# ---- sample puzzles ----
easy_puzzle = "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3.."
hard_puzzle = "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......"

TIME_LIMIT = 20

if __name__ == '__main__':
    show = args.disp
    sat = args.ec
    if sat:
        print("*Running in SAT solver mode...*")

    if args.test == 0:
        run_single(easy_puzzle, TIME_LIMIT, show=True, sat_mode=sat)
    elif args.test == 1:
        run_single(hard_puzzle, TIME_LIMIT, show=True, sat_mode=sat)
    elif args.test == 2:
        run_batch("problems/easy.txt", TIME_LIMIT, 2, show, sat)
    elif args.test == 3:
        run_batch("problems/hard.txt", TIME_LIMIT, 30, show, sat)
