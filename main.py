import copy
import heapq
import time
import itertools
import functools

level="""
#########
#       #
#@    $ #
#.   $ ##
#.  #   #
#########
"""

def get_level(level):
    with open(f'./levels/{level}.txt') as f:
        return f.read()

class Position():
    solved_positions = set()
    positions_explored = 0
    position_2box_filtered = 0
    time_start = time.time()

    def __init__(self, level=None):
        if level is not None:
            self._board, self._goals, self._boxes, self._player = Position.init(level)
        else:
            self._board, self._goals, self._boxes, self._player = [[]], set(), dict(), None
        self._last_moved_box = None
        self._update()
        if level is not None:
            self._move_history = []
            self._original_normalized_player = self._normalized_player
            self._build_perfect_goals()
            self._build_1box_dead_positions()
            self._build_2box_dead_positions()

    def _add_perfect_goals(self):
        if len(self._boxes) == 1:
            return
        new_perfect_goals = set()
        for nrow, ncol in (self._goals - self._perfect_goals):
            for walls in [((0, 1), (1, 0)),
                          ((-1, 0), (0, 1)),
                          ((-1, 0), (0, -1)),
                          ((0, -1), (1, 0))]:
                c = 0
                for wall_dy, wall_dx in walls:
                    if self._board[nrow + wall_dy][ncol + wall_dx] == 1 or ((nrow + wall_dy, ncol + wall_dx) in self._perfect_goals and (nrow + wall_dy, ncol + wall_dx) in self._boxes):
                        c += 1
                if c == 2:
                    new_perfect_goals.add((nrow, ncol))
        self._perfect_goals.update(new_perfect_goals)

    def _build_perfect_goals(self):
        self._perfect_goals = set()
        for nrow, ncol in self._goals:
            for walls in [((0, 1), (1, 0)),
                          ((-1, 0), (0, 1)),
                          ((-1, 0), (0, -1)),
                          ((0, -1), (1, 0))]:
                c = 0
                for wall_dy, wall_dx in walls:
                    c += self._board[nrow + wall_dy][ncol + wall_dx]
                if c == 2:
                    self._perfect_goals.add((nrow, ncol))

    def _build_1box_dead_positions(self):
        self._one_box_deads = set()
        for nrow in range(len(self._board)):
            for ncol in range(len(self._board[0])):
                if self._board[nrow][ncol] == 0:
                    position = Position.copy(self)
                    position._player = ((nrow, ncol))
                    position.set_boxes({(nrow, ncol)})
                    is_solved, _ = Position.solve(position)
                    if not is_solved:
                        self._one_box_deads.add((nrow, ncol))

    def _build_2box_dead_positions(self):
        self._two_box_deads = dict()
        candidate_squares = []
        for nrow in range(len(self._board)):
            for ncol in range(len(self._board[0])):
                if self._board[nrow][ncol] == 0:
                    if (nrow, ncol) not in self._one_box_deads:
                        candidate_squares.append((nrow, ncol))
        print(len(candidate_squares), len(candidate_squares) * (len(candidate_squares) - 1) / 2)
        for idx, ((nrow1, ncol1), (nrow2, ncol2)) in enumerate(itertools.combinations(candidate_squares, 2)):
            if idx % 250 == 0:
                print(idx)
            players_viewed = dict()
            all_positions_are_solvable = True
            for player_nrow in range(len(self._board)):
                for player_ncol in range(len(self._board[0])):
                    if self._board[player_nrow][player_ncol] == 0:
                        if (player_nrow, player_ncol) not in [(nrow1, ncol1), (nrow2, ncol2)]:
                            position = Position.copy(self)
                            position._player = ((player_nrow, player_ncol))
                            position.set_boxes({(nrow1, ncol1), (nrow2, ncol2)})
                            position._last_moved_box = (nrow1, ncol1)
                            result = True
                            if position._normalized_player in players_viewed:
                                result = players_viewed[position._normalized_player]
                            else:
                                if Position.is_solvable(position):
                                    result, _ = Position.solve(position, check_reduced=False)
                                    if not result:
                                        all_positions_are_solvable = False
                                players_viewed[position._normalized_player] = result
                            players_viewed[(player_nrow, player_ncol)] = result
            if not all_positions_are_solvable:
                self._two_box_deads[((nrow1, ncol1), (nrow2, ncol2))] = players_viewed
            else:
                Position.solved_positions.add(position)

    def _update(self):
        self._player_board, self._normalized_player = Position.get_player_reachable_squares(self)

    def __hash__(self):
        return hash(frozenset(self._boxes).union(self._normalized_player))

    def __eq__(self, other):
        return self._boxes.keys() == other._boxes.keys() and self._normalized_player == other._normalized_player

    @staticmethod
    def init(level):
        board, goals, boxes, player = [], set(), dict(), None
        for nrow, line in enumerate(level.strip().splitlines()):
            board.append([])
            for ncol, char in enumerate(line):
                if char in ['-', '#']:
                    board[nrow].append(1)
                else:
                    board[nrow].append(0)
                    if char == '.':
                        goals.add((nrow, ncol))
                    elif char == '$':
                        boxes[(nrow, ncol)] = (0, (nrow, ncol)) # counting number of moves
                    elif char == '@':
                        player = (nrow, ncol)
        return board, goals, boxes, player

    @staticmethod
    def get_player_reachable_squares(position):
        top_left_y, top_left_x = 1000000, 1000000
        res = [[0]*len(position._board[0]) for nrow in range(len(position._board))]
        if position._player is not None:
            py, px = position._player
            queue = [(py, px)]
            seen = set()
            while queue:
                py, px = queue.pop()
                if (py, px) in seen:
                    continue
                seen.add((py, px))
                res[py][px] = 1
                if py < top_left_y or (py == top_left_y and px < top_left_x):
                    top_left_y, top_left_x = py, px
                for move in Position.get_player_moves(position, (py, px)):
                    queue.append(move)
        return res, (top_left_y, top_left_x)

    @staticmethod
    def get_player_moves(position, player=None):
        if player is None:
            player = position._player
        py, px = player
        if position._board[py - 1][px] == 0 and (py - 1, px) not in position._boxes:
            yield (py - 1, px)
        if position._board[py + 1][px] == 0 and (py + 1, px) not in position._boxes:
            yield (py + 1, px)
        if position._board[py][px - 1] == 0 and (py, px - 1) not in position._boxes:
            yield (py, px - 1)
        if position._board[py][px + 1] == 0 and (py, px + 1) not in position._boxes:
            yield (py, px + 1)

    @staticmethod
    def get_pushable_boxes(position):
        boxes = position._boxes.keys() - position._perfect_goals
        for by, bx in boxes:
            if position._player_board[by][bx + 1]:
                if (by, bx - 1) not in position._boxes:
                    if position._board[by][bx - 1] == 0:
                        yield (by, bx, 'l')
            if position._player_board[by + 1][bx]:
                if (by - 1, bx) not in position._boxes:
                    if position._board[by - 1][bx] == 0:
                        yield (by, bx, 'u')
            if position._player_board[by - 1][bx]:
                if (by + 1, bx) not in position._boxes:
                    if position._board[by + 1][bx] == 0:
                        yield (by, bx, 'd')
            if position._player_board[by][bx - 1]:
                if (by, bx + 1) not in position._boxes:
                    if position._board[by][bx + 1] == 0:
                        yield (by, bx, 'r')

    def set_boxes(self, boxes):
        self._boxes = {}
        for box in boxes:
            self._boxes[box] = (0, box)
        self._update()

    def push_box(self, box_y, box_x, direction):
        value, orig_pos = self._boxes.pop((box_y, box_x))
        dy, dx = {'u': (-1, 0), 'd': (1, 0), 'l': (0, -1), 'r': (0, 1)}[direction]
        self._boxes[(box_y + dy, box_x + dx)] = (value + 1, orig_pos)
        self._last_moved_box = (box_y + dy, box_x + dx)
        self._player = (box_y, box_x)
        if self._last_moved_box in self._perfect_goals:
            self._add_perfect_goals()
        self._update()
        self._move_history.append((box_y, box_x, direction))

    @staticmethod
    def copy(position):
        res = Position(level=None)
        res._board = position._board
        res._player = position._player
        res._goals = position._goals
        res._boxes = copy.copy(position._boxes)

        res._player_board = position._player_board
        res._normalized_player = position._normalized_player
        res._original_normalized_player = position._original_normalized_player
        res._one_box_deads = position._one_box_deads
        res._two_box_deads = position._two_box_deads if hasattr(position, '_two_box_deads') else dict()
        res._perfect_goals = copy.copy(position._perfect_goals)
        res._move_history = copy.copy(position._move_history)
        return res

    @staticmethod
    def is_solved(position):
        return len(position._boxes.keys() - position._goals) == 0
        #return len(set(position._boxes.keys()).intersection(position._goals)) >= min(8, len(position._boxes))

    @staticmethod
    def is_reduced(position):
        num_dead_boxes = sum(num_moves == 0 for num_moves, orig_pos in position._boxes.values())
        num_dead_boxes += sum((pos == orig_pos and num_moves != 0) for pos, (num_moves, orig_pos) in position._boxes.items())
        if position._perfect_goals.intersection(position._boxes):
            if num_dead_boxes + len(position._perfect_goals.intersection(position._boxes)) == len(position._boxes):
                if position._player_board[position._original_normalized_player[0]][position._original_normalized_player[1]]:
                    return True
        return False

    solvable = {}

    @staticmethod
    def precalc_dead_masks():
        masks = [#[[0, 0, 0],  # 1 wall, 2 box
                 # [0, 0, 1],
                 # [0, 1, 0]],
                 [[1, 1, 0],
                  [2, 0, 0],
                  [0, 0, 0]],
                 [[1, 2, 0],
                  [1, 0, 0],
                  [0, 0, 0]],
                 [[2, 2, 0],
                  [2, 0, 0],
                  [0, 0, 0]],
                 [[1, 2, 0],
                  [2, 0, 0],
                  [0, 0, 0]],
                 [[2, 1, 0],
                  [2, 0, 0],
                  [0, 0, 0]],
                 [[2, 2, 0],
                  [1, 0, 0],
                  [0, 0, 0]],
                 [[0, 0, 1],
                  [0, 0, 2],
                  [0, 1, 0]]]
        Position.masks = []
        for mask in masks:
            total = sum([value != 0 for row in mask for value in row])
            for rotation in range(4):
                walls = []
                boxes = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if mask[1 + dy][1 + dx] == 1:  # wall
                            walls.append((dy, dx))
                        elif mask[1 + dy][1 + dx] == 2:  # box
                            boxes.append((dy, dx))
                Position.masks.append((tuple(walls), tuple(boxes), total))
                if rotation < 3:  # no need to rotate on last iteration
                    mask[0][0], mask[0][2], mask[2][2], mask[2][0] = mask[0][2], mask[2][2], mask[2][0], mask[0][0]
                    mask[0][1], mask[1][2], mask[2][1], mask[1][0] = mask[1][2], mask[2][1], mask[1][0], mask[0][1]

    @staticmethod
    def is_solvable(position):
        boxes = { position._last_moved_box } - position._goals  # consider only last moved box
        if position._last_moved_box not in position._goals:
            last_moved_box_y, last_moved_box_x = position._last_moved_box
            for walls, boxes, total in Position.masks:
                c = 0
                for wall_dy, wall_dx in walls:
                    c += position._board[last_moved_box_y + wall_dy][last_moved_box_x + wall_dx]
                for box_dy, box_dx in boxes:
                    c += (last_moved_box_y + box_dy, last_moved_box_x + box_dx) in position._boxes
                if c == total:
                    return False
        return True

    @staticmethod
    def solve(position, check_reduced=True, priority_func=None, limit_positions_explored=0):
        def priority(position, counter):
            if len(position._boxes) <= 2:
                return counter
            num_dead_boxes = sum(num_moves == 0 for num_moves, orig_pos in position._boxes.values())
            num_pushed_boxes = len(position._goals.intersection(position._boxes.keys()))
            return (-num_dead_boxes, -num_pushed_boxes, -counter)

        if priority_func is not None:
            priority = priority_func
        states = [(0, position)]
        seen_positions = set()
        reduced_positions = set()
        counter = 0
        while states:
            counter += 1
            Position.positions_explored += 1
            if limit_positions_explored:
                if Position.positions_explored > limit_positions_explored:
                    return False, None
            time_end = time.time()
            Position.positions_per_sec = Position.positions_explored / (time_end - Position.time_start + 1)
            metric, position = heapq.heappop(states)
            if position in Position.solved_positions: # TODO: remove, this is only for 2box_deads
                return True, None
            if Position.is_solved(position):
                return True, position
            if check_reduced and Position.is_reduced(position):
                #print('Reduced!!!')
                #print(position)
                if position not in reduced_positions:
                    reduced_positions.add(position)
                    #print('Number of reduced positions: ', len(reduced_positions))
                    states.clear()
                    seen_positions.clear()
            for box_y, box_x, direction in Position.get_pushable_boxes(position):
                counter += 1
                dy, dx = {'u': (-1, 0), 'd': (1, 0), 'l': (0, -1), 'r': (0, 1)}[direction]
                if (box_y+dy, box_x+dx) in position._one_box_deads:
                    continue
                two_box_unsolvable = False
                for (box1, box2), player_pos in position._two_box_deads.items():
                    if (box_y + dy, box_x + dx) in (box1, box2):
                        if (box_y + dy, box_x + dx) == box2:
                            box1, box2 = box2, box1
                        if box2 in (position._boxes.keys() - {(box_y, box_x)}):
                            try:
                                if not player_pos[(box_y, box_x)]:
                                    two_box_unsolvable = True
                                    Position.position_2box_filtered += 1
                                    break
                            except:
                                print('exception')
                                print(position, direction, box_y, box_x, player_pos)
                                pass
                if two_box_unsolvable:
                    continue

                new_position = Position.copy(position)
                new_position.push_box(box_y, box_x, direction)
                if new_position not in seen_positions:
                    seen_positions.add(new_position)
                    if Position.is_solvable(new_position):
                        heapq.heappush(states, (priority(new_position, counter), new_position))

            if 0 and Position.positions_explored % 10000 == 0 and len(position._boxes) == len(position._goals):
                print(f'Performance: {Position.positions_per_sec} positions per second')
                print('metric: ', metric)
                print('number of cached positions: ', len(seen_positions))
                print('number of positions in queue: ', len(states))
                print('positions viewed: ', Position.positions_explored)
                print('positions filtered due to 2box: ', Position.position_2box_filtered, 100 * Position.position_2box_filtered/(Position.positions_explored+Position.position_2box_filtered))
                print('number of box pushed: ', sum(map(lambda x: x[0], position._boxes.values())))
                print(position)
        return False, None

    def __str__(self):
        res = ''
        for nrow, row in enumerate(self._board):
            res += '\n'
            for ncol, value in enumerate(self._board[nrow]):
                if self._player == (nrow, ncol):
                    res += '@'
                elif (nrow, ncol) in self._boxes:
                    if self._boxes[(nrow,ncol)][0] == 0 or self._boxes[(nrow,ncol)][1] == (nrow,ncol):
                        res += '?'
                    else:
                        res += '$'
                elif (nrow, ncol) in self._perfect_goals:
                    res += '='
                elif (nrow, ncol) in self._goals:
                    res += '.'
                elif value:
                    res += '#'
                #elif self._player_board[nrow][ncol]:
                #    res += ' '
                elif (nrow, ncol) in self._one_box_deads:
                    res += 'x'
                #elif (nrow, ncol) == self._normalized_player:
                #    res += '+'
                else:
                    res += ' '
        return res

Position.precalc_dead_masks()

level = get_level(4)
position = Position(level)

#is_solved, solved_position = Position.solve(position)
#print('Positions viewed: ', Position.positions_explored)
#if is_solved:
#    print(solved_position._move_history)

def priority_func(position, counter, order, signs):
    if len(position._boxes) <= 2:
        return counter
    num_dead_boxes = sum(num_moves == 0 for num_moves, orig_pos in position._boxes.values())
    num_pushed_boxes = len(position._goals.intersection(position._boxes.keys()))
    res = [num_dead_boxes, num_pushed_boxes, counter]
    for idx, sign in enumerate(signs):
        res[idx] *= sign
    res = [res[i] for i in order]
    return tuple(res)



metrics = ('num_dead_boxes', 'num_pushed_boxes', 'counter')
orders = list(itertools.permutations([0,1,2], 3))
signs = list(itertools.product([-1,1], repeat=3))
signs = ((-1,-1,-1), (-1,-1,1))

min_duration = 1000000
min_positions_explored = 100000000
win_strategy = None
results = []
for order in orders:
    for sign in signs:
        Position.positions_explored = 0
        strategy =','.join((['','','-'][sign[i]] + metrics[i]) for i in order)
        time_start = time.time()
        is_solved, solved_position = Position.solve(position, priority_func=functools.partial(priority_func, order=order, signs=sign), limit_positions_explored=min_positions_explored*2)
        duration = time.time() - time_start
        print(strategy)
        print('Positions viewed: ', Position.positions_explored)
        print('Time: ', duration)
        min_positions_explored = min(min_positions_explored, Position.positions_explored)
        metric = (Position.positions_explored, duration, strategy)
        results.append(metric)

print('Sorted by exploration:')
for value in sorted(results):
    print(value)
print('Sorted by timings:')
for value in sorted(results, key=lambda x: x[1]):
    print(value)

#print('Winning strategy: ', win_strategy)
#print('Best time: ', min_duration)
#print('Best exploration: ', min_positions_explored)
