# scheduler
Linear programming-based software for deciding what tasks to do on each day

A Schedule manages a set of Blocks and Tasks. A Block is a typical calendar element you might pull from an ical file--they represent concrete commitments in a person's schedule. A Task, on the other hand, is something one *could* put time into but that hasn't yet been allocated any time. Tasks come in two varieties: OngoingTasks and CompletableTasks. An OngoingTask is a task that can take an indefinite amount of time, like "practice saxophone"--an OngoingTask has a parameter representing how many hours a week one would like to put into it, and another representing the cost (in the objective function of the LP) of not hitting that weekly target. A CompletableTask is a task that can be completed after a finite amount of time, like "write a novel". A CompletableTask stores the estimated total amount of time required to complete the task, its due date (if it has one), and any prerequisite CompletableTasks. All Tasks have an associated vector of scores. Scores are used to create a good daily balance of activity type. For instance, one score might represent how much exercise is involved in one hour of doing a task. Another might be a measure of how productive that task is toward long-term life goals. Daily score targets and costs for missing them are stored in the Schedule.

To optimally allocate time for each task, a preliminary algorithm sets the due dates for all tasks listed as prerequisites to other tasks. Task and Block data are then fed into an Optimizer, which links to the default PuLP LP solver. The decision variables for the LP are x_11, ..., x_mn, where x_ij represents how many hours to spend doing task i on day j.

# installation

1. Install Python 3
2. `pip3 install -r requirements.txt`
3. Test with `python3 scheduler_test.py`