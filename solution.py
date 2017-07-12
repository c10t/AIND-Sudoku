import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.ERROR)

assignments = []


def assign_value(values, box, value):
    """
    Please use this function to update your values dictionary!
    Assigns a value to a given box. If it updates the board record it.
    """

    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values

    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values


def naked_twins(values):
    """Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}

    Returns:
        the values dictionary with the naked twins eliminated from peers.
    """

    # Find all instances of naked twins
    # Eliminate the naked twins as possibilities for their peers

    rows = 'ABCDEFGHI'
    cols = '123456789'
    boxes = cross(rows, cols)
    row_units = [cross(r, cols) for r in rows]
    col_units = [cross(rows, c) for c in cols]
    square_units = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
    diag_units = [[r + c for (r, c) in zip(rows, cols)], [r + c for (r, c) in zip(rows, cols[::-1])]]

    unitlist = row_units + col_units + square_units + diag_units
    units = dict((s, [u for u in unitlist if s in u]) for s in boxes)

    # search twins
    twins_candidates = [key for key in values.keys() if len(values[key]) == 2]

    for candidate in twins_candidates:
        for unit in units[candidate]:
            candidate_value = values[candidate]

            # skip if candidate_value replaced by other candidate_value
            if len(candidate_value) < 2:
                continue

            pair = [key for key in unit if key != candidate and values[key] == candidate_value]
            # if twins are found, eliminate twins from other boxes in the unit
            if len(pair) == 1:
                logging.debug('twins {}, {} are found on the unit {}'.format(candidate, pair[0], unit))
                for box in unit:
                    if box == candidate or box == pair[0]:
                        continue
                    if len(values[box]) < 2:
                        continue
                    replaced_value = values[box].replace(candidate_value[0], '').replace(candidate_value[1], '')
                    logging.debug('apply naked twins: before/after: {} / {}'.format(values[box], replaced_value))
                    values = assign_value(values, box, replaced_value)

    # TODO: reduce duplicated key pair like ['E4', 'E5'] and ['E5', 'E4']
    return values


def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [s + t for s in A for t in B]


def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Args:
        grid(string) - A grid in string form.
    Returns:
        A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """

    rows = 'ABCDEFGHI'
    cols = '123456789'
    boxes = cross(rows, cols)

    values = []
    all_digits = '123456789'

    for c in grid:
        if c == '.':
            values.append(all_digits)
        elif c in all_digits:
            values.append(c)

    assert len(values) == 81
    return dict(zip(boxes, values))


def display(values):
    """
    Display the values as a 2-D grid.
    Args:
        values(dict): The sudoku in dictionary form
    """
    rows = 'ABCDEFGHI'
    cols = '123456789'
    boxes = cross(rows, cols)

    width = 1 + max(len(values[s]) for s in boxes)
    line = '+'.join(['-' * (width * 3)] * 3)

    for r in rows:
        print(''.join(values[r + c].center(width) + ('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)

    return


def eliminate(values):
    """Eliminate values from peers of each box with a single value.

    Go through all the boxes, and whenever there is a box with a single value,
    eliminate this value from the set of values of all its peers.
    
    Args:
        values: The sudoku in dictionary form
    Returns:
        The sudoku in dictionary form after eliminating values
    """
    rows = 'ABCDEFGHI'
    cols = '123456789'
    boxes = cross(rows, cols)
    row_units = [cross(r, cols) for r in rows]
    col_units = [cross(rows, c) for c in cols]
    square_units = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
    diag_units = [[r + c for (r, c) in zip(rows, cols)], [r + c for (r, c) in zip(rows, cols[::-1])]]

    unitlist = row_units + col_units + square_units + diag_units
    units = dict((s, [u for u in unitlist if s in u]) for s in boxes)
    peers = dict((s, set(sum(units[s], []))-set([s])) for s in boxes)

    assigned = [key for key in values.keys() if len(values[key]) == 1]

    for key in assigned:
        for peer in peers[key]:
            values[peer] = values[peer].replace(values[key], '')

    return values


def only_choice(values):
    """
    Finalize all values that are the only choice for a unit.

    Go through all the units, and whenever there is a unit with a value
    that only fits in one box, assign the value to this box.
    
    Args:
        values: The sudoku in dictionary form
    Returns:
        The sudoku in dictionary form after filling in only choices.
    """
    rows = 'ABCDEFGHI'
    cols = '123456789'
    row_units = [cross(r, cols) for r in rows]
    col_units = [cross(rows, c) for c in cols]
    square_units = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
    diag_units = [[r + c for (r, c) in zip(rows, cols)], [r + c for (r, c) in zip(rows, cols[::-1])]]

    unitlist = row_units + col_units + square_units + diag_units

    for unit in unitlist:
        for digit in '123456789':
            d_places = [box for box in unit if digit in values[box]]
            if len(d_places) == 1:
                values[d_places[0]] = digit

    return values


def reduce_puzzle(values):
    """
    Reduce possible values by applying some strategies.
    
    Args:
        values: The sudoku in dictionary form
    Returns:
        The sudoku in dictionary form after reducing, or False if it is stalled.
    """
    stalled = False
    while not stalled:
        # Check how many boxes have a determined value
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])

        # Use the Eliminate Strategy
        values = eliminate(values)

        # Use the Only Choice Strategy
        values = only_choice(values)

        # Use the Naked Twins Strategy
        values = naked_twins(values)

        # Check how many boxes have a determined value, to compare
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])

        # If no new values were added, stop the loop.
        stalled = solved_values_before == solved_values_after

        # Sanity check, return False if there is a box with zero available values:
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False

    return values


def search(values):
    """
    Solve a sudoku using depth-first search and propagation
    
    Args:
        values: The sudoku in dictionary form
    Returns:
        The sudoku in dictionary form after searching, or False if it fails.
    """

    rows = 'ABCDEFGHI'
    cols = '123456789'
    boxes = cross(rows, cols)

    # Using depth-first search and propagation, create a search tree and solve the sudoku.
    # First, reduce the puzzle using the previous function
    values = reduce_puzzle(values)
    if values is False:
        return False
    if all(len(values[s]) == 1 for s in boxes):
        return values

    # Choose one of the unfilled squares with the fewest possibilities
    n, s = min((len(values[s]), s) for s in boxes if len(values[s]) > 1)

    # Now use recursion to solve each one of the resulting sudokus,
    # and if one returns a value (not False), return that answer!
    for value in values[s]:
        new_sudoku = values.copy()
        new_sudoku[s] = value
        attempt = search(new_sudoku)
        if attempt:
            return attempt


def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """

    return search(grid_values(grid))

if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(solve(diag_sudoku_grid))

    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
