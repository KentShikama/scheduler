package scheduler;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * The Schedule class -- a central place for storing and managing info on the Tasks to
 * be scheduled, as well as Blocks (blocks of already-scheduled time).
 * 
 * @author jason2e
 *
 */
public class Schedule {
	
	private double maxDailyHours;
	private List<Task> tasks;
	private List<Integer> completableIndices;
	private List<Integer> ongoingIndices;
	private Map<Task, Integer> task2index;
	private List<Block> permBlocks;
	
	private double[][] currentSchedule;
	
	private Optimizer optimizer;
	
	public final double SHIFT_COST = 50;
	public final double TIME_COST = 100000;
	public final double UNSMOOTH_COST = 100;
	public final double[] DAILY_SCORE_TARGETS = {100,100,100,100,100,100};
	
	public Schedule()
	{
		maxDailyHours = 15.0;
		permBlocks = new ArrayList<Block>();
		tasks = new ArrayList<Task>();
		completableIndices = new ArrayList<Integer>();
		ongoingIndices = new ArrayList<Integer>();
		task2index = new HashMap<Task,Integer>();
		optimizer = null;
	}
	
	
	public void addTask(Task t)
	{
		if(!task2index.containsKey(t))
		{
			tasks.add(t);
			task2index.put(t, tasks.size() - 1);
		}
	}
	
	public void addCompletable(CompletableTask t)
	{
		addTask(t);
		completableIndices.add(task2index.get(t));
	}
	
	public void addOngoing(OngoingTask t)
	{
		addTask(t);
		ongoingIndices.add(task2index.get(t));
	}
	
	public void addBlock(Block b)
	{
		permBlocks.add(b);
		addTask(b.getTask());
	}
	
	public void orderedToDoList(List<CompletableTask> todo)
	{
		Iterator<CompletableTask> iter = todo.iterator();
		CompletableTask first;
		CompletableTask second;
		if(iter.hasNext())
			first = iter.next();
		else return;
		addCompletable(first);
		while(iter.hasNext())
		{
			second = iter.next();
			addCompletable(second);
			second.getPrereqs().add(first);
			first = second;
		}
	}
	
	public void assignDues(int budgetDays)
	{
		for (int i :  completableIndices)
		{
			((CompletableTask)tasks.get(i)).assignDueDays(budgetDays);
		}
	}
	
	/**
	 * This method builds and executes an Optimizer object, and returns the resulting
	 * schedule.
	 * @return a 2D array whose [i][j] element indicates hours spent doing task i on day j.
	 */
	public double[][] makeSchedule(LocalDateTime start, int budgetDays)
	{
		assignDues(budgetDays);
		
		int[][] whether = new int[tasks.size()][budgetDays];
		for (int i = 0; i < tasks.size(); i++)
		{
			for (int j = 0; j < budgetDays; j++)
			{
				whether[i][j] = 1;
			}
		}
		optimizer = new Optimizer(
					maxDailyHours,
					tasks.size(),
					budgetDays,
					this.makeDues(start),			//1 for tomorrow, 0 if tasks[i] is not a dueTask
					this.makeTotalHours(),
					this.makeWeekHours(),	 			//for each task
					Task.NUM_SCORES,
					DAILY_SCORE_TARGETS, 			//size numScores
					this.makeHourScores(), 			//numTasks by numScores
					this.makeXPrime(budgetDays),
					this.permTaskTime(start, budgetDays),
					Task.MISS_DAILY_SCORE_COSTS,	//size numScores
					SHIFT_COST,
					TIME_COST,
					UNSMOOTH_COST,
					this.makeMissWeekTargetCosts(), //size numTasks
					whether
					);
		currentSchedule = optimizer.optimize();
		return currentSchedule;
	}
	
	
	/**
	 * @return currentSchedule the 2D representation of the optimal schedule
	 */
	public double[][] getCurrentSchedule()
	{
		return currentSchedule;
	}
	
	//a bunch of methods for making the instance variables for the Optimizer
	
	private double[][] permTaskTime(LocalDateTime start, int budgetDays)
	{
		double[][] out = new double[tasks.size()][budgetDays];
		for (Block b : permBlocks)
		{
			for (int j = 0; j < budgetDays; j++)
			{
				if (start.plusDays(j).toLocalDate().equals(b.getStart().toLocalDate()))
				{
					out[task2index.get(b.getTask())][j] = b.getHours();
				}
				
				else if (b.fixedRepeat() && start.plusDays(j).isAfter(b.getStart()) &&
						b.isRepeatDay(start.plusDays(j)))
				{
					out[task2index.get(b.getTask())][j] = b.getHours();
				}
			}
		}
		return out;
	}
	
	private double[][] makeHourScores()
	{
		double[][] hourScores = new double[tasks.size()][Task.NUM_SCORES];
		for (int i = 0; i < tasks.size(); i++)
		{
			hourScores[i] = tasks.get(i).getScores();
		}
		return hourScores;
	}
	
	private int[] makeDues(LocalDateTime start)
	{
		int[] dues = new int[tasks.size()];
		for (int i : completableIndices)
		{
			if (((CompletableTask)tasks.get(i)).isDueTask())
			{
				dues[i] = start.toLocalDate().until(((CompletableTask)tasks.get(i)).getDue().toLocalDate()).getDays();
			}
		}
		return dues;
	}
	
	private double[][] makeXPrime(int budgetDays)
	{
		double[][] xPrime = new double[tasks.size()][budgetDays];
		if (currentSchedule == null) return xPrime;
		for (int i = 0; i < tasks.size() && i < currentSchedule.length; i++)
		{
			for (int j = 0; j < budgetDays && j < currentSchedule[i].length; j++)
			{
				xPrime[i][j] = currentSchedule[i][j];
			}
		}
		return xPrime;
	}
	
	private double[] makeTotalHours()
	{
		double[] totalHours = new double[tasks.size()];
		for (int i : completableIndices)
		{
			totalHours[i] = ((CompletableTask)tasks.get(i)).getTotalHours();
		}
		return totalHours;
	}
	
	private double[] makeWeekHours()
	{
		double[] weekHours = new double[tasks.size()];
		for (int i : ongoingIndices)
		{
			weekHours[i] = ((OngoingTask)tasks.get(i)).getWeekHours();
		}
		return weekHours;
	}
	
	private double[] makeMissWeekTargetCosts()
	{
		double[] missWeeklyTargetCosts = new double[tasks.size()];
		for (int i : ongoingIndices)
		{
			missWeeklyTargetCosts[i] = ((OngoingTask)tasks.get(i)).getMissWeekTargetCost();
		}
		return missWeeklyTargetCosts;
	}
	
	
	
}
