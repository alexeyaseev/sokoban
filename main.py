import copy
import heapq
import time
import itertools

level = """
######
#@   #
###  #
## $ #
# .# #
######
"""
level="""
##############
#..  #     ###
#..  #       #
#..  # ####  #
#..      ##  #
#..  # #    ##
######$##    #
### $      @ #
###    #     #
##############
"""
level = """
##############
#..  #     ###
#..  #       #
#..  # ####  #
#..$     ##@ #
#..  # #    ##
###### ##    #
###        $ #
###    #     #
##############
"""
level="""
#################
#########     ###
##########$   ###
######### $ # ###
#...   ##$      #
##       @      #
#.  $  ##########
#################
"""
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
    position_viewed = 0
    position_filtered = 0
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
                    #or (nrow + wall_dy, ncol + wall_dx) == self._last_moved_box:
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
                    is_solved, _ = Position.solve(position, debug=False)
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
                                    result, _ = Position.solve(position, debug=False, check_reduced=False)
                                    if not result:
                                        all_positions_are_solvable = False
                                players_viewed[position._normalized_player] = result
                            players_viewed[(player_nrow, player_ncol)] = result
            if not all_positions_are_solvable:
                self._two_box_deads[((nrow1, ncol1), (nrow2, ncol2))] = players_viewed
            else:
                Position.solved_positions.add(position)

    def _update(self):
        #previous_player_board = self._player_board if hasattr(self, '_player_board') else None
        #previous_player_board_set = set()

        self._player_board, self._normalized_player = Position.get_player_reachable_squares(self)

        # self._ignore_position_check = False
        # if previous_player_board is not None:
        #     for nrow in range(len(previous_player_board)):
        #         for ncol in range(len(previous_player_board[0])):
        #             if previous_player_board[nrow][ncol] == 1:
        #                 previous_player_board_set.add((nrow, ncol))
        #     current_player_board_set = set()
        #     for nrow in range(len(self._player_board)):
        #         for ncol in range(len(self._player_board[0])):
        #             if self._player_board[nrow][ncol] == 1:
        #                 current_player_board_set.add((nrow, ncol))
        #     if current_player_board_set == previous_player_board_set.union({ self._player }):
        #         self._ignore_position_check = True
        #self._blocked_regions = Position._get_blocked_regions(self)

    @staticmethod
    def _get_blocked_regions(position):
        regions = []
        def start_region(nrow, ncol):
            region = set()
            queue = [(nrow, ncol)]
            seen = set()
            while queue:
                py, px = queue.pop()
                if (py, px) in seen:
                    continue
                seen.add((py, px))
                region.add((py, px))
                for move in Position.get_player_moves(position, (py, px)):
                    queue.append(move)
            return region

        for nrow in range(len(position._player_board)):
            for ncol in range(len(position._player_board[0])):
                if position._player_board[nrow][ncol] == 0:
                    if position._board[nrow][ncol] == 0:
                        if (nrow, ncol) not in position._boxes:
                            if not any((nrow, ncol) in region for region in regions):
                                region = start_region(nrow, ncol)
                                regions.append(region)
        return regions

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
        #not_matched_boxes = position._boxes.keys() - position._goals
        #matched_boxes = set(position._boxes.keys()).intersection(position._goals)
        #boxes = list(sorted(not_matched_boxes, key=lambda x: position._boxes[x])) + list(matched_boxes)
        boxes = position._boxes.keys() - position._perfect_goals
        moves = []
        for by, bx in boxes:
            if position._player_board[by][bx + 1]:
                if (by, bx - 1) not in position._boxes:
                    if position._board[by][bx - 1] == 0:
                        yield (by, bx, 'l')
                        # if (by, bx - 1) in position._perfect_goals:
                        #     moves.insert(0, (by, bx, 'l'))
                        # else:
                        #     moves.append((by, bx, 'l'))
            if position._player_board[by + 1][bx]:
                if (by - 1, bx) not in position._boxes:
                    if position._board[by - 1][bx] == 0:
                        yield (by, bx, 'u')
                        # if (by - 1, bx) in position._perfect_goals:
                        #     moves.insert(0, (by, bx, 'u'))
                        # else:
                        #     moves.append((by, bx, 'u'))
            if position._player_board[by - 1][bx]:
                if (by + 1, bx) not in position._boxes:
                    if position._board[by + 1][bx] == 0:
                        yield (by, bx, 'd')
                        # if (by + 1, bx) in position._perfect_goals:
                        #     moves.insert(0, (by, bx, 'd'))
                        # else:
                        #     moves.append((by, bx, 'd'))
            if position._player_board[by][bx - 1]:
                if (by, bx + 1) not in position._boxes:
                    if position._board[by][bx + 1] == 0:
                        yield (by, bx, 'r')
        #                 if (by, bx + 1) in position._perfect_goals:
        #                     moves.insert(0, (by, bx, 'r'))
        #                 else:
        #                     moves.append((by, bx, 'r'))
        # return moves

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
        #print(len(self._move_history))

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
        #res._blocked_regions = position._blocked_regions
        return res

    @staticmethod
    def is_solved(position):
        return len(position._boxes.keys() - position._goals) == 0
        return len(set(position._boxes.keys()).intersection(position._goals)) >= min(8, len(position._boxes))

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
        #if frozenset(position._boxes) in Position.solvable:
        #    return Position.solvable[frozenset(position._boxes)]
        #boxes = position._boxes - position._goals  # get only boxes which are not on goals already
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
                    #Position.solvable[frozenset(position._boxes)] = False
                    return False
        return True

    @staticmethod
    def solve(position, debug=True, check_reduced=True):
        def priority_(position):
            return len(position._boxes.keys() - position._goals)
        #def priority(position):
        #    return sum([_col for _row in position._player_board for _col in _row])# + len(position._boxes - position._goals)
        def priority_(position):
            return -time.time_ns()
        def priority_(position):
            return -counter
        def priority(position):
            #return (counter, len(position._boxes - position._goals))
            return (len(position._boxes.keys() - position._goals), -counter)
        def priority(position):
            import statistics
            if len(position._boxes) <= 2:
                return counter
            #stddev = statistics.stdev(position._boxes.values()) ** 2
            num_dead_boxes = sum(num_moves == 0 for num_moves, orig_pos in position._boxes.values())
            num_perfect_pushed_boxes = len(position._perfect_goals.intersection(position._boxes.keys()))
            num_pushed_boxes = len(position._goals.intersection(position._boxes.keys()))
            #return (-num_dead_boxes, -num_perfect_pushed_boxes, -counter)#-num_pushed_boxes, -counter)
            return (-num_dead_boxes, -num_pushed_boxes, -counter)  # -num_pushed_boxes, -counter)
            #max_moves = max(position._boxes.values())
            #min_moves = min(position._boxes.values())
            #return (-num_dead_boxes, len(position._boxes.keys() - position._goals), -counter)
            #v = sum(num_moves == 0 for num_moves in position._boxes.values())
            #return (-round(stddev,1), len(position._boxes.keys() - position._goals), +counter)
            #return -counter

        states = [(0, position)]
        seen_states = set()
        reduced_positions = set()
        counter = 0
        while states:
            Position.position_viewed += 1
            time_end = time.time()
            performance = Position.position_viewed / (time_end - Position.time_start + 1)
            if Position.position_viewed % 10000 == 0:
                print(f'performance: {performance} positions per second')
            metric, position = heapq.heappop(states)
            if position in Position.solved_positions:
                return True, None
            if debug and counter % 10000 == 0:
                print('metric: ', metric)
                print('number of cached positions: ', len(seen_states))
                print('number of positions in queue: ', len(states))
                print('positions viewed: ', Position.position_viewed, ', filtered', Position.position_filtered, 100 * Position.position_filtered/(Position.position_viewed+Position.position_filtered))
                print('positions filtered due to 2box: ', Position.position_2box_filtered, 100 * Position.position_2box_filtered/(Position.position_viewed+Position.position_2box_filtered))
                print(position, sum(map(lambda x: x[0], position._boxes.values())))
                pass
            if Position.is_solved(position):
                #print('Solved!!!')
                if debug:
                    print(position)
                return True, position
            if check_reduced and Position.is_reduced(position):
                if debug:
                    print('Reduced!!!')
                    print(position)
                if position not in reduced_positions:
                    reduced_positions.add(position)
                    print('Number of reduced positions: ', len(reduced_positions))
                    states.clear()
                    seen_states.clear()
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
                                print(position, direction, box_y, box_x, player_pos)
                                pass
                if two_box_unsolvable:
                    continue
                new_position = Position.copy(position)
                new_position.push_box(box_y, box_x, direction)
                #if sum(new_position._boxes.values()) > 400:
                #    Position.position_filtered += 1
                #    continue
                #is_push_box_revertable = False
                #dy, dx = {'u': (-1, 0), 'd': (1, 0), 'l': (0, -1), 'r': (0, 1)}[direction]
                #revert_direction = {'u':'d', 'd':'u', 'l':'r', 'r':'l'}[direction]
                #if (box_y+dy, box_x+dx, revert_direction) in Position.get_pushable_boxes(new_position):
                #    is_push_box_revertable = True
                if new_position not in seen_states:
                    seen_states.add(new_position)
                    #if is_push_box_revertable or new_position._ignore_position_check or Position.is_solvable(new_position):
                    #if is_push_box_revertable or Position.is_solvable(new_position):
                    if Position.is_solvable(new_position):
                        heapq.heappush(states, (priority(new_position), new_position))
            counter += 1
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

level = get_level(9)

position = Position(level)
#position.set_boxes({(2,3), (3,2)})
print(position)
#print(list(Position.get_pushable_boxes(position)))

#a = list(Position.get_pushable_boxes(position))[0]
#position.make_move(*a)
#position.display()

res, position = Position.solve(position)
#print(Position.is_solvable(position))


#print(list(get_available_moves(data, boxes, player)))

#for move in get_available_moves(data, boxes, player):
#    print(move)
#    new_boxes, new_player = make_move(move, boxes)
#    display(data, new_boxes, goals, new_player)
#print(is_solved(boxes, goals))
print('Positions viewed: ', Position.position_viewed)

print(len(position._move_history))
print(position._move_history)