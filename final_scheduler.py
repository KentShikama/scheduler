"""
Created on Sat Sep 15 22:13:26 2018

@author: jason2e
"""

# Next steps:
# randomize basis matrix before solving
# finish Block and RRule
# read in ical to perm_blocks -- use ical package
# transfer perm_blocks to perm_task_time right before makeSchedule()
# transfer perm_blocks and flex_blocks into current_schedule right before makeSchedule()
# approximate block repeats (eg "Do laundry every 6 to 8 days")
# read ordered to-do list into CompletableTasks
# ongoing benchmark -- completable task made from an ongoing task
# block generation:
# algorithm that takes current_schedule and spits out blocks for each day, into flex_blocks
# promotion from flex_blocks to perm_blocks
# merge two schedule objects
# whether_patterns for Tasks (use rrule?)
# repeating Completable with no prereqs
# repeating set of Completables with a single due date with no external prereqs
# c++ branch and bound variant for acheiving min day hours


from pulp import *
from datetime import *
import math
import pickle
import numpy as np

from schedule_utility import (
    hours_to_time_string,
    add_row_of_zeros_before_index,
    delete_first_columns,
    WEEKDAYS,
    ScheduleConstants,
)


class Block(object):
    def __init__(self, name, start, duration, scores, rr, task):
        self.name = name
        self.start = start
        self.duration = duration
        self.window_days = 1
        self.scores = scores
        self.rr = rr
        self.task = task

    def getNext(self):
        if not self.rr.has_next():
            return None
        return Block(
            name=self.name,
            start=self.rr.next(),
            duration=self.duration,
            scores=self.scores,
            rr=self.rr,
            task=self.task,
        )

    def generateTask(self):  # TODO write this
        return self.task


"""
class TimeSet(object):
    def __init__(self, intervals = set()):
        self.intervals = intervals

class TimeInterval(object):

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.duration = end - start
"""

# for blocks only!!
class RRule(object):
    def __init__(self, rr):
        self.rr = rr
        self.index = 0

    def has_next(self):  # TODO write this
        return True

    def next(self):
        self.index += 1
        return self.rr[self.index - 1]


class Task(object):
    def __init__(
        self,
        name="task",
        descr="",
        max_day_hours=24.0,
        max_block_length=24.0,
        min_block_length=10.0 / 60,
        is_batch=True,
        batch_hours=10.0 / 60,
        scores=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    ):
        self.name = name
        self.descr = descr
        self.max_day_hours = max_day_hours
        self.max_block_length = max_block_length
        self.min_block_length = min_block_length
        self.is_batch = is_batch
        if batch_hours <= 0:
            self.batch_hours = 1.0
        else:
            self.batch_hours = batch_hours
        self.scores = scores

    def isBatch(self):
        return self.is_batch


class CompletableTask(Task):
    def __init__(
        self,
        name="task",
        max_day_hours=24.0,
        max_block_length=24.0,
        min_block_length=10.0 / 60,
        is_batch=False,
        batch_hours=1.0,
        scores=(0, 0, 0, 0, 0, 0),
        due=None,
        total_hours=0,
        prereqs=set(),
    ):
        super(CompletableTask, self).__init__(
            name=name,
            max_day_hours=max_day_hours,
            max_block_length=max_block_length,
            min_block_length=min_block_length,
            is_batch=is_batch,
            batch_hours=batch_hours,
            scores=scores,
        )
        self.due = due
        self.total_hours = total_hours
        self.prereqs = prereqs

    def minDays(self):
        return int(math.ceil(self.total_hours / self.max_day_hours))

    def getHoursFromSquareOne(self):
        return self.__squareOneAux(set())

    def __squareOneAux(self, exclude):
        sum = self.total_hours
        exclude.add(self)
        for t in self.prereqs:
            if t not in exclude:
                sum += t.__squareOneAux(exclude)
        return sum


class OngoingTask(Task):
    def __init__(
        self,
        name,
        max_day_hours,
        max_block_length,
        min_block_length,
        is_batch,
        batch_hours,
        scores,
        week_hours,
        miss_week_cost,
    ):
        super(OngoingTask, self).__init__(
            name=name,
            max_day_hours=max_day_hours,
            max_block_length=max_block_length,
            min_block_length=min_block_length,
            is_batch=is_batch,
            batch_hours=batch_hours,
            scores=scores,
        )
        self.week_hours = week_hours
        self.miss_week_cost = miss_week_cost


class Schedule:
    def __init__(
        self,
        schedule_constants=ScheduleConstants(),
        start=date.today(),
        budget_days=7,
        current_schedule=[],
        perm_task_time=[],
        completables=[],
        ongoings=[],
        flex_blocks=[],
        perm_blocks=[],
    ):
        self.schedule_constants = schedule_constants
        self.NUM_SCORES = len(
            schedule_constants.miss_daily_score_costs
        )  # TODO: Refactor
        self.start = start
        self.budget_days = budget_days
        self.current_schedule = current_schedule
        self.perm_task_time = perm_task_time
        self.completables = completables
        self.ongoings = ongoings
        self.due_dates = dict([(c, c.due) for c in completables])
        self.flex_blocks = flex_blocks
        self.perm_blocks = perm_blocks
        self.cost = -1
        self.is_up_to_date = False
        self._grids = [self.current_schedule, self.perm_task_time]
        self._prereqs_prior_dues = dict()

        # TODO make sure tasks from blocks are included in completables/ongoings

    def has_due_date(self, compl_task):
        return not self.due_dates.get(compl_task) or not (
            self.due_dates[compl_task] is None
        )

    def addCompletables(self, tasks):
        for task in tasks:
            if task not in self.completables:
                for grid in self._grids:
                    add_row_of_zeros_before_index(
                        grid, len(self.completables), self.budget_days
                    )
                self.completables.append(task)
                self.due_dates[task] = task.due
        self.is_up_to_date = False

    def addOngoings(self, tasks):
        for task in tasks:
            if task not in self.ongoings:
                for grid in self._grids:
                    add_row_of_zeros_before_index(grid, len(grid), self.budget_days)
                self.ongoings.append(task)
        self.is_up_to_date = False

    def bringUpToDate(self):
        # move start date
        # delete tasks that were already due
        # delete past columns of grids, add up to budget_days
        today = date.today()
        for grid in self._grids:
            delete_first_columns(grid, self.dateToIndex(today))
            for i in grid:
                i += [0.0 for j in range(self.dateToIndex(today))]
        if self.start < date.today():
            self.start = date.today()
        self.completables = [
            c
            for c in self.completables
            if c.due is None or self.dateToIndex(c.due) <= 0
        ]

    def __str__(self):
        out = ""
        for j in range(self.budget_days):
            out += (
                WEEKDAYS[self.indexToDate(j).weekday()] + " " + str(self.indexToDate(j))
            )
            out, completables_hours = self.__append_completables_to_str(j, out)
            out, ongoings_hours = self.__append_ongoings_to_str(j, out)
            out = self.__append_score_totals_to_str(j, out)
            out = self.__append_total_hours_to_str(
                completables_hours, ongoings_hours, out
            )
            out += "\n\n"
        return out

    def __append_completables_to_str(self, j, out):
        hours = 0
        for i, completable in enumerate(self.completables):
            if self.current_schedule[i][j] > completable.min_block_length:
                out += "\n"
                out += completable.name + " (completable) "
                out += hours_to_time_string(self.current_schedule[i][j])
                hours += self.current_schedule[i][j]
        return out, hours

    def __append_ongoings_to_str(self, j, out):
        hours = 0
        for i, ongoing in enumerate(self.ongoings):
            offset_i = i + len(self.completables)
            if self.current_schedule[offset_i][j] > ongoing.min_block_length:
                out += "\n"
                out += ongoing.name + " (ongoing) "
                out += hours_to_time_string(self.current_schedule[offset_i][j])
                hours += self.current_schedule[offset_i][j]
        return out, hours

    def __append_score_totals_to_str(self, j, out):
        out += "\nscore totals: "
        for s in range(self.NUM_SCORES):
            total = 0
            for i, completable in enumerate(self.completables):
                total += completable.scores[s] * self.current_schedule[i][j]
            for i, ongoing in enumerate(self.ongoings):
                total += (
                    ongoing.scores[s]
                    * self.current_schedule[i + len(self.completables)][j]
                )
            out += str(int(total)) + " "
        return out

    def __append_total_hours_to_str(self, completables_hours, ongoings_hours, out):
        out += "\n"
        total_hours = completables_hours + ongoings_hours
        out += "total time: " + hours_to_time_string(total_hours)
        return out

    def save(self, filename):
        with open(filename, "wb") as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    # Assigns due dates to prerequisite tasks. Original due dates
    # are stored in self._prereqs_prior_dues and should be restored
    # after the schedule is calculated.
    def __assignDues(self):
        self.due_dates = dict([(c, c.due) for c in self.completables])
        returnval = True
        for c in self.completables:
            if self.has_due_date(c):
                if not self.__assignDuesAux(c, dict()):
                    returnval = False

        return returnval

    def __assignDuesAux(self, compl_task, cache):
        if not self.due_dates.get(compl_task):
            return False
        num_days = (self.due_dates[compl_task] - self.start).days
        if num_days < compl_task.minDays():
            return False

        square_one_time = 0
        if cache.get(compl_task):
            square_one_time = cache[compl_task]
        else:
            square_one_time = compl_task.getHoursFromSquareOne()
        cache[compl_task] = square_one_time
        last_days = int(math.floor(num_days * compl_task.total_hours / square_one_time))
        pre_due = self.due_dates[compl_task] - timedelta(days=last_days)
        for p in compl_task.prereqs:
            if self.due_dates[p] is None or pre_due < self.due_dates[p]:
                self.due_dates[p] = pre_due
            if not self.__assignDuesAux(p, cache):
                return False
        return True

    def __make_whether(self):
        whether_dimension = (
            len(self.completables) + len(self.ongoings),
            self.budget_days,
        )
        whether = np.full(whether_dimension, True, dtype=bool)
        for i, completable in enumerate(self.completables):
            startable_index = self.__get_start_index(completable)
            whether[i][:startable_index] = False
        return whether.astype(int).tolist()

    def __get_start_index(self, completable, start_index=0):
        for c in completable.prereqs:
            if not self.has_due_date(c):
                return self.budget_days
            else:
                start_index = max(start_index, self.dateToIndex(self.due_dates[c]) - 1)
        return start_index

    def __makePermTaskTime(self):
        num_tasks = len(self.completables) + len(self.ongoings)
        self.perm_task_time = [
            [0.0 for j in range(self.budget_days)] for i in range(num_tasks)
        ]
        # TODO read in perm_blocks

    def dateToIndex(self, d):
        return (d - self.start).days

    def indexToDate(self, j):
        return self.start + timedelta(days=j)

    # make schedule matrix and store it in current_schedule
    def makeSchedule(self):
        # build the parameters
        num_completables = len(self.completables)
        num_ongoings = len(self.ongoings)
        num_tasks = num_completables + num_ongoings
        compl_batches = [c.batch_hours for c in self.completables]
        ong_batches = [o.batch_hours for o in self.ongoings]
        batches = compl_batches + ong_batches

        # set dues
        self.__assignDues()
        dues = [0 for c in self.completables]
        for i in range(num_completables):
            if self.has_due_date(self.completables[i]):
                dues[i] = self.dateToIndex(self.due_dates[self.completables[i]])

        # make whether
        whether = self.__make_whether()

        total_hours = [c.total_hours for c in self.completables]

        # min_day_hours = [c.min_day_hours for c in completables] + [o.min_day_hours for o in ongoings]

        week_hours = [o.week_hours for o in self.ongoings]

        miss_week_costs = [o.miss_week_cost for o in self.ongoings]

        hour_scores = [c.scores for c in self.completables] + [
            o.scores for o in self.ongoings
        ]

        compl_wheth = [whether[i] for i in range(num_completables)]

        ong_wheth = [whether[i + num_completables] for i in range(num_ongoings)]

        # trim current_schedule to proper dimensions
        temp = [[0.0 for j in range(self.budget_days)] for i in range(num_tasks)]
        for i in range(min(num_tasks, len(self.current_schedule))):
            for j in range(min(self.budget_days, len(self.current_schedule[i]))):
                temp[i][j] = self.current_schedule[i][j]
        self.current_schedule = temp

        self.__makePermTaskTime()

        # build lp

        problem = LpProblem("Schedule", LpMinimize)

        # declare decision variables
        # decision variables express number of batches (both for integer and continuous)
        compl_decisions = [[] for c in self.completables]
        for i in range(num_completables):
            for j in range(self.budget_days):
                if self.completables[i].isBatch():
                    compl_decisions[i].append(
                        LpVariable(
                            self.completables[i].name + str(j),
                            0,
                            self.completables[i].max_day_hours
                            / self.completables[i].batch_hours,
                            LpInteger,
                        )
                    )
                else:
                    compl_decisions[i].append(
                        LpVariable(
                            self.completables[i].name + str(j),
                            0,
                            self.completables[i].max_day_hours
                            / self.completables[i].batch_hours,
                            LpContinuous,
                        )
                    )

        ong_decisions = [[] for o in self.ongoings]
        for i in range(num_ongoings):
            for j in range(self.budget_days):
                if self.ongoings[i].isBatch():
                    ong_decisions[i].append(
                        LpVariable(
                            self.ongoings[i].name + str(j),
                            0,
                            self.ongoings[i].max_day_hours
                            / self.ongoings[i].batch_hours,
                            LpInteger,
                        )
                    )
                else:
                    ong_decisions[i].append(
                        LpVariable(
                            self.ongoings[i].name + str(j),
                            0,
                            self.ongoings[i].max_day_hours
                            / self.ongoings[i].batch_hours,
                            LpContinuous,
                        )
                    )

        x = compl_decisions + ong_decisions

        abval1 = [
            LpVariable(
                name="abval1" + str(j), lowBound=0, upBound=None, cat=LpContinuous
            )
            for j in range(self.budget_days - 1)
        ]

        abval2 = [
            [
                LpVariable("abval2" + str(i) + str(j), 0, None, LpContinuous)
                for j in range(self.budget_days)
            ]
            for i in range(num_tasks)
        ]

        abval3 = [
            [
                LpVariable("abval3" + str(j) + str(s), 0, None, LpContinuous)
                for s in range(self.NUM_SCORES)
            ]
            for j in range(self.budget_days)
        ]

        abval4 = [
            [
                LpVariable("abval4" + str(i) + str(w), 0, None, LpContinuous)
                for w in range(int(self.budget_days / 7))
            ]
            for i in range(num_ongoings)
        ]

        # build objective
        line1 = LpAffineExpression(
            [(a, self.schedule_constants.unsmooth_cost) for a in abval1]
        )

        line2 = lpSum(
            [
                LpAffineExpression(
                    [
                        (
                            x[i][j],
                            self.schedule_constants.time_cost
                            * batches[i]
                            * whether[i][j],
                        )
                        for j in range(self.budget_days)
                    ]
                )
                for i in range(num_tasks)
            ]
        )  # double check this

        line3 = lpSum(
            [
                LpAffineExpression(
                    [
                        (abval2[i][j], self.schedule_constants.shift_cost)
                        for j in range(self.budget_days)
                    ]
                )
                for i in range(num_tasks)
            ]
        )

        line4 = lpSum(
            [
                LpAffineExpression(
                    [
                        (
                            abval3[j][s],
                            self.schedule_constants.miss_daily_score_costs[s],
                        )
                        for s in range(self.NUM_SCORES)
                    ]
                )
                for j in range(self.budget_days)
            ]
        )

        line5 = lpSum(
            [
                LpAffineExpression(
                    [
                        (abval4[i][w], miss_week_costs[i])
                        for w in range(int(self.budget_days / 7))
                    ]
                )
                for i in range(num_ongoings)
            ]
        )

        objective = lpSum([line1, line2, line3, line4, line5])

        problem += objective

        # build constraints

        # due constraints
        for i in range(num_completables):
            if dues[i] > 0:
                exp = LpAffineExpression(
                    [
                        (compl_decisions[i][j], compl_wheth[i][j])
                        for j in range(min(dues[i], self.budget_days))
                    ]
                )
                problem += LpConstraint(
                    e=exp,
                    sense=LpConstraintGE,
                    rhs=int(
                        total_hours[i]
                        / compl_batches[i]
                        * float(min(dues[i], self.budget_days))
                        / dues[i]
                    ),
                )

            exp = LpAffineExpression(
                [
                    (compl_decisions[i][j], compl_batches[i] * compl_wheth[i][j])
                    for j in range(self.budget_days)
                ]
            )
            problem += LpConstraint(e=exp, sense=LpConstraintLE, rhs=total_hours[i])

        # permtask constraints
        for i in range(num_tasks):
            for j in range(self.budget_days):
                exp = LpAffineExpression([(x[i][j], batches[i] * whether[i][j])])
                problem += LpConstraint(
                    e=exp, sense=LpConstraintGE, rhs=self.perm_task_time[i][j]
                )

        # abvals next

        # begin abval1 unsmoothness
        for j in range(self.budget_days - 1):
            l1 = [(x[i][j], batches[i] * whether[i][j]) for i in range(num_tasks)] + [
                (x[i][j + 1], -batches[i] * whether[i][j + 1]) for i in range(num_tasks)
            ]
            l1.append((abval1[j], -1))
            pos = LpAffineExpression(l1)

            l2 = [(x[i][j], -batches[i] * whether[i][j]) for i in range(num_tasks)] + [
                (x[i][j + 1], batches[i] * whether[i][j + 1]) for i in range(num_tasks)
            ]
            l2.append((abval1[j], -1))
            neg = LpAffineExpression(l2)

            problem += LpConstraint(e=pos, sense=LpConstraintLE, rhs=0)
            problem += LpConstraint(e=neg, sense=LpConstraintLE, rhs=0)
        # end abval1

        # abval2 shift from previous schedule
        for i in range(num_tasks):
            for j in range(self.budget_days):
                pos = LpAffineExpression(
                    [(x[i][j], batches[i] * whether[i][j]), (abval2[i][j], -1)]
                )
                neg = LpAffineExpression(
                    [(x[i][j], -batches[i] * whether[i][j]), (abval2[i][j], -1)]
                )

                problem += LpConstraint(
                    e=pos, sense=LpConstraintLE, rhs=self.current_schedule[i][j]
                )
                problem += LpConstraint(
                    e=neg, sense=LpConstraintLE, rhs=-self.current_schedule[i][j]
                )
        # end abval2

        # abval3 daily score targets
        for j in range(self.budget_days):
            for s in range(self.NUM_SCORES):
                l1 = [
                    (x[i][j], hour_scores[i][s] * batches[i] * whether[i][j])
                    for i in range(num_tasks)
                ]
                l1.append((abval3[j][s], -1))
                pos = LpAffineExpression(l1)

                l2 = [
                    (x[i][j], -hour_scores[i][s] * batches[i] * whether[i][j])
                    for i in range(num_tasks)
                ]
                l2.append((abval3[j][s], -1))
                neg = LpAffineExpression(l2)

                problem += LpConstraint(
                    e=pos,
                    sense=LpConstraintLE,
                    rhs=self.schedule_constants.daily_score_targets[s],
                )
                problem += LpConstraint(
                    e=neg,
                    sense=LpConstraintLE,
                    rhs=-self.schedule_constants.daily_score_targets[s],
                )
        # end abval3

        # abval4 weekhours
        for i in range(num_ongoings):
            for w in range(int(self.budget_days / 7)):
                l1 = [
                    (
                        ong_decisions[i][7 * w + d],
                        -ong_batches[i] * ong_wheth[i][7 * w + d],
                    )
                    for d in range(7)
                ]
                l1.append((abval4[i][w], -1))
                pos = LpAffineExpression(l1)

                l2 = [
                    (
                        ong_decisions[i][7 * w + d],
                        ong_batches[i] * ong_wheth[i][7 * w + d],
                    )
                    for d in range(7)
                ]
                l2.append((abval4[i][w], -1))
                neg = LpAffineExpression(l2)

                problem += LpConstraint(e=pos, sense=LpConstraintLE, rhs=-week_hours[i])
                problem += LpConstraint(e=neg, sense=LpConstraintLE, rhs=week_hours[i])
        # end abval4

        # sum day hours constraint
        for j in range(self.budget_days):
            exp = LpAffineExpression(
                [(x[i][j], whether[i][j] * batches[i]) for i in range(num_tasks)]
            )
            problem += LpConstraint(
                e=exp, sense=LpConstraintLE, rhs=self.schedule_constants.max_daily_hours
            )

        problem.solve()
        self.current_schedule = [
            [
                compl_decisions[i][j].value()
                * self.completables[i].batch_hours
                * compl_wheth[i][j]
                for j in range(self.budget_days)
            ]
            for i in range(num_completables)
        ] + [
            [
                ong_decisions[i][j].value()
                * self.ongoings[i].batch_hours
                * ong_wheth[i][j]
                for j in range(self.budget_days)
            ]
            for i in range(num_ongoings)
        ]

        self.cost = value(problem.objective)
        self.is_up_to_date = True
        return problem

    # double check passing parameters directly allows mutability
    # TODO: test this
    def costOfBlock(self, block):
        test_sched = Schedule(  # TODO add the rest here
            start=self.start,
            budget_days=self.budget_days,
            current_schedule=self.current_schedule,
            perm_task_time=self.perm_task_time,
            completables=self.completables,
            ongoings=self.ongoings,
            flex_blocks=self.flex_blocks,
            perm_blocks=self.perm_blocks,
        )
        task = CompletableTask(
            name="test",
            max_day_hours=block.duration,
            max_block_length=block.duration,
            min_block_length=0,
            is_batch=False,
            batch_hours=1.0,
            scores=block.scores,
            due=block.start,
            total_hours=block.duration,
            prereqs=set(),
        )
        test_sched.addCompletables([task])
        assert len(self.completables) == len(test_sched.completables) - 1
        if not test_sched.makeSchedule():
            return float("inf")
        if not self.is_up_to_date:
            self.makeSchedule()
        return test_sched.cost - self.cost
