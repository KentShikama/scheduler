import pickle

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