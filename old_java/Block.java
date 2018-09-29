package scheduler;
import java.time.*;
import java.time.temporal.ChronoUnit;
import java.util.function.Predicate;


/**
 * 
 * Block represents a concrete block of time for performing a particular task. Blocks
 * may have a fixed pattern for repeating, as in a typical calendar app. Blocks might be
 * read in from an ical file so that Schedule will schedule around
 * pre-existing commitments.
 * 
 * @author jason2e
 * 
 */
public class Block {
	
	private Task task;
	private LocalDateTime start;
	private LocalDateTime end;
	private double hours;
	private boolean fixedRepeat;
	private LocalDateTime endDate;
	private Predicate<LocalDateTime> repeatDay;
	
	public Block(Task t, LocalDateTime s, LocalDateTime e)
	{
		task = t;
		start = s;
		end = e;
		hours = ((double)start.until(end, ChronoUnit.MINUTES))/60;
		fixedRepeat = false;
		endDate = null;
		repeatDay = null;
	}
	
	public Block(Task t, LocalDateTime s, LocalDateTime e, LocalDateTime end, Predicate<LocalDateTime> r)
	{
		task = t;
		start = s;
		end = e;
		hours = ((double)start.until(end, ChronoUnit.MINUTES))/60;
		fixedRepeat = true;
		endDate = end;
		repeatDay = r;
	}
	
	public LocalDateTime getStart()
	{
		return start;
	}
	
	public LocalDateTime getEnd()
	{
		return end;
	}
	
	public double getHours()
	{
		return hours;
	}
	
	public boolean fixedRepeat()
	{
		return fixedRepeat;
	}
	
	public boolean isRepeatDay(LocalDateTime ldt)
	{
		return repeatDay.test(ldt);
	}
	
	public static Predicate<LocalDateTime> isOfWeekDays(DayOfWeek[] days) {
	    return d -> isOfWeekDays(d, days);
	}
	
	public static Predicate<LocalDateTime> isOfMonthDates(int[] dates)
	{
		return d -> isOfMonthDates(d, dates);
	}
	
	public static boolean isOfWeekDays(LocalDateTime d, DayOfWeek[] days)
	{
		for(int i = 0; i < days.length; i++)
		{
			if (d.getDayOfWeek() == days[i])
			{
				return true;
			}
		}
		return false;
	}
	
	public static boolean isOfMonthDates(LocalDateTime d, int[] dates)
	{
		for(int i = 0; i < dates.length; i++)
		{
			if (d.getDayOfMonth() == dates[i])
			{
				return true;
			}
		}
		return false;
	}
	
	public static boolean isEveryXFromD(LocalDateTime d, LocalDateTime start, int interval)
	{
		LocalDateTime iter = start.plusDays(0);
		while(iter.isBefore(d))
		{
			if (iter.getDayOfYear() == d.getDayOfYear() && iter.getYear() == d.getYear())
			{
				return true;
			}
			iter.plusDays(interval);
		}
		if (iter.getDayOfYear() == d.getDayOfYear() && iter.getYear() == d.getYear())
		{
			return true;
		}
		return false;
	}
	
	public Task getTask()
	{
		return task;
	}
	
	
}
