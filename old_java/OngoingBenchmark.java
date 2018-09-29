package scheduler;

import java.time.LocalDateTime;

/**
 * OngoingBenchmark represents a concrete goal for an OngoingTask. For instance, if
 * a piano player needs to practice 5 hours to be ready for a concert, they can
 * take their OngoingTask "practice piano" (which they have probably already written)
 * and make an OngoingBenchmark due the day of the concert with totalHours = 5.
 * It can also be used to list an OngoingTask as a prerequisite for another task.
 * @author jason2e
 *
 */
public class OngoingBenchmark extends CompletableTask {
	private OngoingTask task;
	public OngoingBenchmark(OngoingTask t, double totalHours, LocalDateTime due, boolean dueTask) {
		super(t.getName(), t.getMaxDayHours(), totalHours, due, dueTask, t.getScores());
		task = t;
	}
	
	public OngoingTask getOngoingTask()
	{
		return task;
	}
	
}
