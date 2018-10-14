import pickle

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
BIG_M = 99999999.9


class ScheduleConstants:
    def __init__(
        self,
        shift_cost=0.0,
        time_cost=10000.0,
        unsmooth_cost=100.0,
        score_labels=(
            "Productive",
            "Intellectual",
            "Exercise",
            "Outdoors",
            "Social",
            "Fun",
        ),
        daily_score_targets=(700, 200, 50, 200, 200, 2400),
        miss_daily_score_costs=(1000, 200, 300, 200, 200, 50),
        max_daily_hours=24.0,
        min_task_length = 1.0 / 60
    ):
        self.shift_cost = shift_cost
        self.time_cost = time_cost
        self.unsmooth_cost = unsmooth_cost
        self.score_labels = score_labels
        self.daily_score_targets = daily_score_targets
        self.miss_daily_score_costs = miss_daily_score_costs
        self.max_daily_hours = max_daily_hours
        self.min_task_length = min_task_length


def hours_to_time_string(hours):
    return (
        str(int(hours))
        + ":"
        + str(int((hours - int(hours)) * 60) / 10)
        + str(int((hours - int(hours)) * 60) % 10)
    )


def load_schedule(filename):
    with open(filename, "rb") as input:
        return pickle.load(input)


def add_row_of_zeros_before_index(grid, index, num_zeros):
    if len(grid) == 0:
        grid.append([])
    else:
        grid.insert(index, [0.0 for h in range(num_zeros)])


# deletes first J columns of a grid.
# useful for removing past days from schedule
# column J not deleted
def delete_first_columns(grid, J):
    for i in range(len(grid)):
        for j in range(min(len(grid[i]), J)):
            del (grid[i][0])
