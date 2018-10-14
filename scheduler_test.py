from final_scheduler import *

completables = []

ongoings = []


schedule_constants = ScheduleConstants(
    shift_cost=0.0,
    time_cost=15000.0,
    unsmooth_cost=100.0,
    score_labels=("Productive", "Mental", "Exercise", "Outdoors", "Social", "Fun"),
    daily_score_targets=(700, 200, 50, 200, 200, 2400),
    miss_daily_score_costs=(1000, 200, 300, 200, 200, 50),
    max_daily_hours=14.0,
)

schedule = Schedule(
    schedule_constants=schedule_constants,
    start=date.today(),
    budget_days=7,
    current_schedule=[],
    perm_task_time=[],
    completables=[],
    ongoings=[],
    flex_blocks=[],
    perm_blocks=[],
)


start = schedule.start
day = timedelta(days=1)
week = timedelta(days=7)
month = timedelta(days=30)


completables.append(
    CompletableTask(
        name="task1",
        max_day_hours=24,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=0.25,
        scores=(90, 50, 0, 0, 0, 50),
        due=start + day,
        total_hours=2.5,
        prereqs=set(),
    )
)

completables.append(
    CompletableTask(
        name="task2",
        max_day_hours=24,
        max_block_length=24,
        min_block_length=0,
        is_batch=True,
        batch_hours=0.25,
        scores=(100, 0, 0, 0, 10, 0),
        due=start + day,
        total_hours=0.25,
        prereqs=set(),
    )
)

completables.append(
    CompletableTask(
        name="task3",
        max_day_hours=24,
        max_block_length=24,
        min_block_length=0,
        is_batch=True,
        batch_hours=0.25,
        scores=(100, 0, 0, 0, 10, 0),
        due=start + 5 * day,
        total_hours=0.25,
        prereqs=set(),
    )
)

completables.append(
    CompletableTask(
        name="task4",
        max_day_hours=4,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=0.5,
        scores=(100, 5, 0, 0, 5, 0),
        due=start + 3 * day,
        total_hours=4,
        prereqs=set(),
    )
)

completables.append(
    CompletableTask(
        name="task5",
        max_day_hours=24,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=0.25,
        scores=(85, 50, 0, 0, 0, 10),
        due=start + 3 * day,
        total_hours=6,
        prereqs=set(),
    )
)

completables.append(
    CompletableTask(
        name="task6",
        max_day_hours=24,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=0.75,
        scores=(100, 50, 0, 0, 0, 50),
        due=start + timedelta(days=1),
        total_hours=0.75,
        prereqs=set(),
    )
)

completables.append(
    CompletableTask(
        name="task7",
        max_day_hours=24,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=0.75,
        scores=(100, 50, 0, 0, 0, 50),
        due=start + timedelta(days=8),
        total_hours=5,
        prereqs=set(),
    )
)

ongoings.append(
    OngoingTask(
        name="task8",
        max_day_hours=3,
        max_block_length=24,
        min_block_length=0,
        is_batch=True,
        batch_hours=0.25,
        scores=(5, 0, 100, 0, 0, 0),
        week_hours=1.5,
        miss_week_cost=100,
    )
)

ongoings.append(
    OngoingTask(
        name="task9",
        max_day_hours=3,
        max_block_length=24,
        min_block_length=0,
        is_batch=True,
        batch_hours=1.0 / 3,
        scores=(5, 0, 100, 0, 0, 0),
        week_hours=1.5,
        miss_week_cost=100,
    )
)

ongoings.append(
    OngoingTask(
        name="task10",
        max_day_hours=6,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=1.0 / 4,
        scores=(10, 15, 0, 0, 30, 20),
        week_hours=7.0,
        miss_week_cost=500,
    )
)

ongoings.append(
    OngoingTask(
        name="task11",
        max_day_hours=6,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=1.0 / 4,
        scores=(10, 15, 0, 0, 30, 30),
        week_hours=7.0,
        miss_week_cost=500,
    )
)

ongoings.append(
    OngoingTask(
        name="task12",
        max_day_hours=3,
        max_block_length=24,
        min_block_length=0,
        is_batch=True,
        batch_hours=1.5,
        scores=(5, 0, 0, 0, 10, 10),
        week_hours=1.5,
        miss_week_cost=500,
    )
)

ongoings.append(
    OngoingTask(
        name="task13",
        max_day_hours=6,
        max_block_length=24,
        min_block_length=0,
        is_batch=False,
        batch_hours=0.5,
        scores=(0, 0, 0, 0, 5, 80),
        week_hours=3.0,
        miss_week_cost=100,
    )
)

ongoings.append(
    OngoingTask(
        name="task14",
        max_day_hours=1.0,
        max_block_length=24,
        min_block_length=0,
        is_batch=True,
        batch_hours=1.0,
        scores=(0, 0, 100, 100, 10, 50),
        week_hours=3,
        miss_week_cost=0,
    )
)

ongoings.append(
    OngoingTask(
        name="task15",
        max_day_hours=5,
        max_block_length=2,
        min_block_length=0,
        is_batch=False,
        batch_hours=1.0,
        scores=(5, 2, 2, 0, 5, 30),
        week_hours=3.5,
        miss_week_cost=10000,
    )
)

ongoings.append(
    OngoingTask(
        name="task16",
        max_day_hours=1.5,
        max_block_length=1,
        min_block_length=0,
        is_batch=False,
        batch_hours=1.0,
        scores=(5, 2, 2, 0, 5, 75),
        week_hours=3.5,
        miss_week_cost=10000,
    )
)


schedule.addCompletables(completables)
schedule.addOngoings(ongoings)


schedule.makeSchedule()


print(schedule)
print(LpStatus[schedule.makeSchedule().status])
