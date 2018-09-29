package scheduler;

/**
 * Task is an abstract class representing an item to be scheduled.
 * @author jason2e
 */
public abstract class Task {
	public static final int NUM_SCORES = 6;
	private String name;
	protected double maxDayHours = 24;
	
	
	//Scores per hour
	public static final double[] MISS_DAILY_SCORE_COSTS = {50,100,75,30,30,40};
	protected double[] scores = new double[NUM_SCORES];
	public Task(String name, double maxDayHours, double[] scores)
	{
		this.name = name;
		this.maxDayHours = maxDayHours;
		this.scores = scores;
	}
	public String getName()
	{
		return name;
	}
	public String toString()
	{
		return name;
	}
	public double[] getScores()
	{
		return scores;
	}
}
