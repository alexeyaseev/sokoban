def priority_(position):
    return len(position._boxes.keys() - position._goals)


# def priority(position):
#    return sum([_col for _row in position._player_board for _col in _row])# + len(position._boxes - position._goals)
def priority_(position):
    return -time.time_ns()


def priority_(position):
    return -counter


def priority(position):
    # return (counter, len(position._boxes - position._goals))
    return (len(position._boxes.keys() - position._goals), -counter)


def priority(position):
    import statistics
    if len(position._boxes) <= 2:
        return counter
    # stddev = statistics.stdev(position._boxes.values()) ** 2
    num_dead_boxes = sum(num_moves == 0 for num_moves, orig_pos in position._boxes.values())
    num_perfect_pushed_boxes = len(position._perfect_goals.intersection(position._boxes.keys()))
    num_pushed_boxes = len(position._goals.intersection(position._boxes.keys()))
    # return (-num_dead_boxes, -num_perfect_pushed_boxes, -counter)#-num_pushed_boxes, -counter)
    return (-num_dead_boxes, -num_pushed_boxes, -counter)  # -num_pushed_boxes, -counter)
    # max_moves = max(position._boxes.values())
    # min_moves = min(position._boxes.values())
    # return (-num_dead_boxes, len(position._boxes.keys() - position._goals), -counter)
    # v = sum(num_moves == 0 for num_moves in position._boxes.values())
    # return (-round(stddev,1), len(position._boxes.keys() - position._goals), +counter)
    # return -counter
