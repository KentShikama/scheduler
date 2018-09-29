package scheduler;

import java.time.*;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * CompletableTask represents a task that can be completed in a finite amount of time.
 * Examples include projects and chores. A CompletableTask can also have a nonempty set
 * of prerequisite CompletableTasks that must be done before it can be started. Prereqs
 * have their due dates determined automatically by Schedule.
 * @author jason2e
 *
 */
public class CompletableTask extends Task
{
	protected boolean dueTask;
	protected LocalDateTime due;
	protected double totalHours; //leave blank if not discrete or dueTask
	protected double totalHoursUncertainty;
	protected boolean allAtOnce;
	
	protected Set<CompletableTask> prereqs;
	
	
	public CompletableTask(String name, double maxDayHours, double totalHours, LocalDateTime due, boolean dueTask, double[] scores)
	{
		super(name, maxDayHours, scores);
		this.totalHours = totalHours;
		this.due = due;
		this.dueTask = dueTask;
		prereqs = new HashSet<CompletableTask>();
	}
	public int minDays()
	{
		return (int)Math.ceil(totalHours/maxDayHours);
	}
	
	public boolean isDueTask()
	{
		return dueTask;
	}
	
	
	public void assignDueDays(int timeBudgetDays)
	{
		assignDuesAux(timeBudgetDays, new HashMap<CompletableTask, Double>());
	}
	
	/**
	 * gives due dates to prerequisites of dueTasks
	 * 
	 * @return success of the operation
	 */
	private boolean assignDuesAux(int timeBudget, Map<CompletableTask, Double> cache)
	{
		if (dueTask)
		{
			if (timeBudget < this.minDays())
			{
				return false;
			}
			double squareOneTime;
			if (cache.containsKey(this))
			{
				squareOneTime = cache.get(this);
			}
			else
			{
				squareOneTime = getHoursFromSquareOne();
			}
			int lastDays = (int)Math.ceil(timeBudget * totalHours / (squareOneTime));
			LocalDateTime preDue = due.minusDays(lastDays);
			for (CompletableTask p : prereqs)
			{
				p.dueTask = true;
				p.pushUpDueDate(preDue);
				if(!p.assignDuesAux(timeBudget - lastDays, cache))
					return false;
			}
			return true;
		}
		return false;
	}
	
	public void pushUpDueDate(LocalDateTime date)
	{
		if (due == null || due.isAfter(date))
		{
			due = date;
		}
	}
	
	public double getTotalHours()
	{
		return totalHours;
	}
	
	public double getHoursFromSquareOne()
	{
		return this.squareOneAux(new HashSet<CompletableTask>());
	}
	
	protected double squareOneAux(Set<CompletableTask> exclude)
	{
		double sum = totalHours; 
		exclude.add(this);
		for (CompletableTask t : prereqs)
		{
			if(!exclude.contains(t))
			{
				sum += t.squareOneAux(exclude);
			}
		}
		return sum;
	}
	
	public LocalDateTime getDue()
	{
		return due;
	}

	public void addPrereq(CompletableTask t)
	{
		prereqs.add(t);
	}

	public Set<CompletableTask> getPrereqs() {
		return prereqs;
	}

}