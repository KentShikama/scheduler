package scheduler;

import java.util.ArrayList;
import com.quantego.clp.*;


/**
 * The Optimizer class. This is where the data from a Schedule is fed into the linear
 * program that finds an optimal schedule.
 * 
 * @author jason2e
 *
 */
public class Optimizer {
	private double maxDailyHours; 
	private int numTasks;
	private int numDays;
	private int[] dues;				//1 for tomorrow, 0 if tasks[i] is not a dueTask
	private double[] totalHours;
	private double[] minDayHours; //for each task, minimum hours if chosen to do on a day
	private double[] weekHours; //for each task
	private int numScores;
	private double[] dailyScoreTargets; //size numScores
	private double[][] hourScores; //numTasks by numScores
	private double[][] xPrime;
	private double[][] permTaskTime;
	private double[] missDailyTargetCosts;	//size numScores
	private double shiftCost;
	private double timeCost;
	private double unsmoothCost;
	private double[] missWeeklyTargetCosts; //size numTasks
	private int[][] whether; //0s and 1s
	
	
	public Optimizer(
		double maxDailyHours,
		int numTasks,
		int numDays,
		int[] dues,						//1 for tomorrow, 0 if tasks[i] is not a dueTask
		double[] totalHours,
		double[] weekHours,	 			//for each task
		int numScores,
		double[] dailyScoreTargets, 	//size numScores
		double[][] hourScores, 			//numTasks by numScores
		double[][] xPrime,
		double[][] permTaskTime,
		double[] missDailyTargetCosts,	//size numScores
		double shiftCost,
		double timeCost,
		double unsmoothCost,
		double[] missWeeklyTargetCosts, //size numTasks
		int[][] whether
		)				//0s and 1s
	{
		this.maxDailyHours = maxDailyHours;
		this.numTasks = numTasks;
		this.numDays = numDays;
		this.dues = dues;					//1 for tomorrow, 0 if tasks[i] is not a dueTask
		this.totalHours = totalHours;
		this.weekHours = weekHours;			//for each task
		this.numScores = numScores;
		this.dailyScoreTargets = dailyScoreTargets; 	//size numScores
		this.hourScores = hourScores;			//numTasks by numScores
		this.xPrime = xPrime;
		this.permTaskTime = permTaskTime;
		this.missDailyTargetCosts = missDailyTargetCosts;	//size numScores
		this.shiftCost = shiftCost;
		this.timeCost = timeCost;
		this.unsmoothCost = unsmoothCost;
		this.missWeeklyTargetCosts = missWeeklyTargetCosts; //size numTasks
		this.whether = whether;
	}
	
	/**
	 * If the instance fields are properly initialized, this method builds and solves the LP,
	 * while printing it and its final status to standard output.
	 * @return a 2D array of values; output[i][j] is the amount of time spent doing task i on day j.
	 */
 	public double[][] optimize()
	{
		/*
		 * Decision variables:
		 * -x[i][j] hours of task i on day j
		 * -abval1[i][j]
		 * -abval2[i][j]
		 * -abval3[i][j]
		 * -abval4[i][j]
		*/
		CLP clp = new CLP();
		CLPVariable[][] x = new CLPVariable[numTasks][numDays];
		CLPVariable[] abval1 = new CLPVariable[numDays - 1];
		CLPVariable[][] abval2 = new CLPVariable[numTasks][numDays];
		CLPVariable[][] abval3 = new CLPVariable[numDays][numScores];
		CLPVariable[][] abval4 = new CLPVariable[numTasks][numDays/7];
		
		 /* Minimize 
		 * (1) unsmoothCost * sum_(j=1)^(numDays - 1) absval1[j] //|sum day j - sum day j-1|
		 * (2) + timeCost * sum_(i=1)^numTasks [sum_(j=1)^numDays whether[i][j] * x[i][j]]
		 * (3) + shiftCost * sum_(i=1)^numTasks [sum_(j=1)^numDays absval2(whether[i][j] * x[i][j] - xPrime[i][j])]
		 * (4) + sum_(j=1)^numDays [sum_(m=1)^numTargets [missTargetCost[m] * absval3(sum_(i=1)^numTasks[i.get(m) * whether[i][j]x[i][j]] - target[m])]
		 * (5) + sum_(i=1)^numTasks [missWeeklyTargetCost[i] * sum_(w=0)^(numDays/7 - 1) [absval4(i.get(hoursPerWeek) - sum_(d=1)^7 [whether[i][zw+d] x[i][7 * w + d]])]]
		 */
		CLPExpression objective = clp.createExpression();
		//line 1
		for (int j = 0; j < numDays - 1; j++)
		{
			abval1[j] = clp.addVariable();
			objective.add(unsmoothCost, abval1[j]);
		}
		//line 2
		for (int i = 0; i < numTasks; i++)
		{
			for (int j = 0; j < numDays; j++)
			{
				x[i][j] = clp.addVariable();
				objective.add(timeCost * whether[i][j], x[i][j]);
			}
		}
		//line 3
		for (int i = 0; i < numTasks; i++)
		{
			for (int j = 0; j < numDays; j++)
			{
				abval2[i][j] = clp.addVariable();
				objective.add(shiftCost, abval2[i][j]);
			}
		}
		//line 4
		for (int j = 0; j < numDays; j++)
		{
			for (int m = 0; m < numScores; m++)
			{
				abval3[j][m] = clp.addVariable();
				objective.add(missDailyTargetCosts[m], abval3[j][m]);
			}
		}
		//line 5
		for (int i = 0; i < numTasks; i++)
		{
			for (int w = 0; w < numDays/7; w++)
			{
				abval4[i][w] = clp.addVariable();
				objective.add(missWeeklyTargetCosts[i], abval4[i][w]);
			}
		}
		
		objective.asObjective();
		
		ArrayList<CLPExpression> constraints = new ArrayList<CLPExpression>();
		
		
		//due constraints
		for (int i = 0; i < numTasks; i++)
		{
			if (dues[i] > 0)//good
			{
				constraints.add(clp.createExpression());
				for (int j = 0; j < dues[i] && j < numDays; j++)
				{
					constraints.get(constraints.size() - 1).add(whether[i][j], x[i][j]);
				}
				constraints.get(constraints.size() - 1).geq(totalHours[i] * ((double) Math.min(dues[i], numDays))/dues[i]);
			}
		}
		
		
		//permtask constraints
		for (int i = 0; i < numTasks; i++)
		{
			for (int j = 0; j < numDays; j++)
			{
				constraints.add(clp.createExpression());
				constraints.get(constraints.size() - 1).add(whether[i][j], x[i][j]);
				constraints.get(constraints.size() - 1).geq(permTaskTime[i][j]);
			}
		}
		
		//abvals next
		
		//begin abval1
		for (int j = 0; j < numDays - 1; j++)
		{
			CLPExpression pos = clp.createExpression();
			CLPExpression neg = clp.createExpression();
			for (int i = 0; i < numTasks; i++)
			{
				pos.add(whether[i][j], x[i][j]);
				pos.add(-whether[i][j+1], x[i][j+1]);
				neg.add(-whether[i][j], x[i][j]);
				neg.add(whether[i][j+1], x[i][j + 1]);
			}
			pos.add(-1, abval1[j]);
			neg.add(-1, abval1[j]);
			
			pos.leq(0);
			neg.leq(0);
			
			constraints.add(pos);
			constraints.add(neg);
		}
		//end abval1
		
		//begin abval2
		for (int i = 0; i < numTasks; i++)
		{
			for (int j = 0; j < numDays; j++)
			{
				constraints.add(clp.createExpression());
				constraints.get(constraints.size() - 1).add(whether[i][j], x[i][j]);
				constraints.get(constraints.size() - 1).add(-1, abval2[i][j]);
				constraints.get(constraints.size() - 1).leq(xPrime[i][j]);
				
				constraints.add(clp.createExpression());
				constraints.get(constraints.size() - 1).add(-whether[i][j], x[i][j]);
				constraints.get(constraints.size() - 1).add(-1, abval2[i][j]);
				constraints.get(constraints.size() - 1).leq(-xPrime[i][j]);
			}
		}
		//end abval2
		
		//begin abval3
		for (int j = 0; j < numDays; j++)
		{
			for (int m = 0; m < numScores; m++)
			{
				CLPExpression pos = clp.createExpression();
				CLPExpression neg = clp.createExpression();
				
				for (int i = 0; i < numTasks; i++)
				{
					pos.add(hourScores[i][m] * whether[i][j], x[i][j]);
					neg.add(-hourScores[i][m] * whether[i][j], x[i][j]);
				}
				pos.add(-1,abval3[j][m]);
				neg.add(-1, abval3[j][m]);
				pos.leq(dailyScoreTargets[m]);
				neg.leq(-dailyScoreTargets[m]);
				constraints.add(pos);
				constraints.add(neg);
			}
		}
		
		//abval4 weekhours
		for (int i = 0; i < numTasks; i++)
		{
			for (int w = 0; w < numDays/7; w++)
			{
				CLPExpression pos = clp.createExpression();
				CLPExpression neg = clp.createExpression();
				pos.add(-1, abval4[i][w]);
				neg.add(-1, abval4[i][w]);
				for (int d = 0; d < 7; d++)
				{
					pos.add(-whether[i][7 * w + d], x[i][7 * w + d]);
					neg.add(whether[i][7 * w + d], x[i][7 * w + d]);
				}
				pos.leq(-weekHours[i]);
				neg.leq(weekHours[i]);
				constraints.add(pos);
				constraints.add(neg);
			}
		}
		
		//maxDailyHours
		for (int j = 0; j < numDays; j++)
		{
			constraints.add(clp.createExpression());
			for (int i = 0; i < numTasks; i++)
			{
				constraints.get(constraints.size() - 1).add(whether[i][j], x[i][j]);
			}
			constraints.get(constraints.size() - 1).leq(maxDailyHours);
		}
		
		
		// >= 0
		for (int i = 0; i < numTasks; i++)
		{
			for (int j = 0; j < numDays; j++)
			{
				constraints.add(clp.createExpression());
				constraints.get(constraints.size() - 1).add(1, x[i][j]);
				constraints.get(constraints.size() - 1).geq(0);
			}
		}
		
		clp.printModel();
		CLP.STATUS status = clp.minimize();
		System.out.println(status);
		
		
		 /* Subject to
		 * DONE dueTasks sum to total hours by their duedate
		 * DONE x[i][j] >= i.get(minHours) for every j
		 * DONE whether[i][j] * x[i][j] >= permTaskTime[i][j]
		 * DONE sum_(i=1)^(numTasks)[whether[i][j] * x[i][j]] - sum_(i=1)^(numTasks)[whether[i][j+1] * x[i][j+1]] <= abval1[j]
		 * DONE -sum_(i=1)^(numTasks)[whether[i][j] * x[i][j]] + sum_(i=1)^(numTasks)[whether[i][j+1] * x[i][j+1]] <= abval1[j]
		 * DONE whether[i][j] * x[i][j] - xPrime[i][j] <= abval2[i][j]
		 * DONE -whether[i][j] * x[i][j] + xPrime[i][j] <= abval2[i][j]
		 * DONE sum_(i=1)^numTasks[i.get(m) * whether[i][j]x[i][j]] - target[m] <= abval3[j][m]
		 * DONE -sum_(i=1)^numTasks[i.get(m) * whether[i][j]x[i][j]] + target[m] <= abval3[j][m]
		 * DONE - abval4[i][w] - sum_(d=1)^7 [whether[i][zw+d] x[i][7 * w + d]] <=  - i.get(hoursPerWeek)
		 * DONE -abval4[i][w] + sum_(d=1)^7 [whether[i][zw+d] x[i][7 * w + d]] <= i.get(hoursPerWeek)
		 * DONE maximum 10 hrs in a day
		 * DONE all variables >=0
		 */
		//transfer output to arrays
		double[][] output = new double[numTasks][numDays];
		for (int i = 0; i < numTasks; i++)
		{
			for (int j = 0; j < numDays; j++)
			{
				output[i][j] = whether[i][j] * x[i][j].getSolution();
			}
				
		}
		return output;
	}
	
	

	public int getNumDays() {
		return numDays;
	}

	public void setNumDays(int numDays) {
		this.numDays = numDays;
	}

	public double[][] getxPrime() {
		return xPrime;
	}

	public void setxPrime(double[][] xPrime) {
		this.xPrime = xPrime;
	}

	public double[] getDailyScoreTargets() {
		return dailyScoreTargets;
	}

	public void setDailyScoreTargets(double[] dailyScoreTargets) {
		this.dailyScoreTargets = dailyScoreTargets;
	}

	public double[] getMissDailyTargetCosts() {
		return missDailyTargetCosts;
	}

	public void setMissDailyTargetCosts(double[] missDailyTargetCosts) {
		this.missDailyTargetCosts = missDailyTargetCosts;
	}

	public double getShiftCost() {
		return shiftCost;
	}

	public void setShiftCost(double shiftCost) {
		this.shiftCost = shiftCost;
	}

	public double getTimeCost() {
		return timeCost;
	}

	public void setTimeCost(double timeCost) {
		this.timeCost = timeCost;
	}

	public double getUnsmoothCost() {
		return unsmoothCost;
	}

	public void setUnsmoothCost(double unsmoothCost) {
		this.unsmoothCost = unsmoothCost;
	}

	public double[] getMissWeeklyTargetCosts() {
		return missWeeklyTargetCosts;
	}

	public void setMissWeeklyTargetCosts(double[] missWeeklyTargetCosts) {
		this.missWeeklyTargetCosts = missWeeklyTargetCosts;
	}


	public double getMaxDailyHours() {
		return maxDailyHours;
	}


	public void setMaxDailyHours(double maxDailyHours) {
		this.maxDailyHours = maxDailyHours;
	}


	public int getNumTasks() {
		return numTasks;
	}


	public void setNumTasks(int numTasks) {
		this.numTasks = numTasks;
	}


	public int[] getDues() {
		return dues;
	}


	public void setDues(int[] dues) {
		this.dues = dues;
	}


	public double[] getTotalHours() {
		return totalHours;
	}


	public void setTotalHours(double[] totalHours) {
		this.totalHours = totalHours;
	}


	public double[] getMinDayHours() {
		return minDayHours;
	}


	public void setMinDayHours(double[] minDayHours) {
		this.minDayHours = minDayHours;
	}


	public double[] getWeekHours() {
		return weekHours;
	}


	public void setWeekHours(double[] weekHours) {
		this.weekHours = weekHours;
	}


	public int getNumScores() {
		return numScores;
	}


	public void setNumScores(int numScores) {
		this.numScores = numScores;
	}


	public double[][] getHourScores() {
		return hourScores;
	}


	public void setHourScores(double[][] hourScores) {
		this.hourScores = hourScores;
	}


	public double[][] getPermTaskTime() {
		return permTaskTime;
	}

	public void setPermTaskTime(double[][] permTaskTime) {
		this.permTaskTime = permTaskTime;
	}


	public int[][] getWhether() {
		return whether;
	}


	public void setWhether(int[][] whether) {
		this.whether = whether;
	}
	
}
