# ai.py — the brains of the sudoku solver
# uses constraint propagation + backtracking search
# also has a SAT encoder/decoder for the extra credit portion

from __future__ import print_function
from game import (peer_map, all_cells, valid_nums, make_domains,
                  apply_clues, BLOCK_SIZE, GRID_SIZE)
import copy


class AI:
    def __init__(self):
        pass

    # --- constraint propagation ---
    # keep eliminating values from peers until nothing changes
    # returns False if we hit a dead end (some cell has zero candidates)
    def _run_propagation(self, domains):
        progress = True
        while progress:
            progress = False
            for cell in all_cells:
                if len(domains[cell]) != 1:
                    continue
                fixed_val = domains[cell][0]
                # knock this value out of every peer's candidate list
                for neighbor in peer_map[cell]:
                    if fixed_val in domains[neighbor]:
                        domains[neighbor] = [v for v in domains[neighbor] if v != fixed_val]
                        if len(domains[neighbor]) == 0:
                            return False  # contradiction
                        progress = True
        return True

    # --- recursive search with backtracking ---
    # picks the most constrained cell (fewest candidates), tries each value
    def _search(self, domains):
        # first, propagate as much as we can
        if not self._run_propagation(domains):
            return None

        # check if we're done
        if all(len(domains[c]) == 1 for c in all_cells):
            return domains

        # grab unsolved cells and pick the one with the fewest options (MRV heuristic)
        unsolved = [c for c in all_cells if len(domains[c]) > 1]
        target = min(unsolved, key=lambda c: len(domains[c]))

        # try each candidate value
        for guess in domains[target]:
            branch = copy.deepcopy(domains)
            branch[target] = [guess]
            result = self._search(branch)
            if result is not None:
                return result

        return None  # all guesses failed, backtrack

    # --- main entry point ---
    def solve(self, puzzle):
        domains = make_domains()
        apply_clues(domains, puzzle)
        answer = self._search(domains)
        # fall back to partially-solved domains if somehow no solution found
        return answer if answer is not None else domains

    # =========================================================
    # SAT encoding / decoding below (extra credit)
    # =========================================================

    def sat_encode(self, problem):
        """
        Convert the sudoku puzzle into a CNF formula (DIMACS format string).
        Each cell+value pair gets its own boolean variable.
        """
        n = len(valid_nums)
        cell_idx = {cell: i for i, cell in enumerate(all_cells)}

        # set up domains with clues applied
        domains = make_domains()
        apply_clues(domains, problem)

        cnf = []
        total_vars = len(all_cells) * n

        # -- at-least-one and at-most-one value per cell --
        for cell in all_cells:
            base = cell_idx[cell] * n
            # at least one value must be true
            cnf.append([base + (valid_nums.index(v) + 1) for v in valid_nums])
            # no two values can both be true
            for a in range(n):
                for b in range(a + 1, n):
                    cnf.append([-(base + a + 1), -(base + b + 1)])

        # -- group constraints (rows, cols, blocks) --
        row_groups, col_groups, blk_groups = {}, {}, {}
        for cell in all_cells:
            r, c = cell
            row_groups.setdefault(r, []).append(cell)
            col_groups.setdefault(c, []).append(cell)
            blk_groups.setdefault((r // BLOCK_SIZE, c // BLOCK_SIZE), []).append(cell)

        for group_dict in [row_groups, col_groups, blk_groups]:
            for members in group_dict.values():
                for vi in range(n):
                    var_ids = [cell_idx[s] * n + (vi + 1) for s in members]
                    # at least one cell in the group has this value
                    cnf.append(var_ids)
                    # at most one cell in the group has this value
                    for p in range(len(members)):
                        for q in range(p + 1, len(members)):
                            cnf.append([-var_ids[p], -var_ids[q]])

        # -- unit clauses for pre-filled cells --
        for cell, vals in domains.items():
            if len(vals) == 1:
                lit = valid_nums.index(vals[0]) + 1
                cnf.append([cell_idx[cell] * n + lit])

        # build the DIMACS string
        header = "c Sudoku CNF — {} vars, {} clauses\n".format(total_vars, len(cnf))
        header += "p cnf {} {}\n".format(total_vars, len(cnf))
        body = "\n".join(" ".join(str(l) for l in clause) + " 0" for clause in cnf)
        return header + body + "\n"

    def sat_decode(self, assignments):
        """
        Take the SAT solver's variable assignments and map them back
        to a sudoku solution (dict of cell -> [value]).
        """
        n = len(valid_nums)
        cell_idx = {cell: i for i, cell in enumerate(all_cells)}
        solution = {cell: [] for cell in all_cells}

        for cell in all_cells:
            base = cell_idx[cell]
            for vi in range(n):
                var_num = base * n + (vi + 1)
                if assignments.get(var_num, False):
                    solution[cell] = [valid_nums[vi]]
                    break

        return solution
