package scheduler;

/**
 * OngoingTask represents a task that cannot be completed in a finite length of time.
 * Examples include exercise and skills practice. An OngoingTask might have a target
 * length of time to spend on it each week and an associated cost for missing that target.
 * Those fields should be set to zero if there is no weekly target.
 * @author jason2e
 *
 */
public class OngoingTask extends Task
{
	private double hoursPerWeekTarget;
	private double missWeeklyTargetCost;
	public OngoingTask(String name, double maxDayHours, double[] scores, double hoursPerWeekTarget, double missWeeklyTargetCost)
	{
		super(name, maxDayHours, scores);
		this.hoursPerWeekTarget = hoursPerWeekTarget;
		this.missWeeklyTargetCost = missWeeklyTargetCost;
	}
	public double getWeekHours() {
		return hoursPerWeekTarget;
	}
	public double getMissWeekTargetCost() {
		return missWeeklyTargetCost;
	}
	public double getMaxDayHours() {
		return maxDayHours;
	}
	
}
