import java.util.*;
import java.io.*;
import java.net.*;
import java.lang.reflect.*;
//work on both terms together algo !
class Scheduler
{
	private static Node<TimeSet> tmp1;
	private static Course crcN;
	private static int CID=-1;
	private static Schedule sch;
	public static void main(String[] args) 
	{
		final int favorableTimes[]={19}, priorities[]={0,1,2,3,4,5};
		final String[] courses={"csc196F","mat137Y","mat223F","phl101Y","eco101F"}; // y1t1
		//final String[] courses={"csc148S","csc165S","mat137Y","mat224S","phl101Y"}; // y1t2
	    sch=new Schedule(courses,favorableTimes,priorities);
	    if(!sch.getCourseData())System.exit(0);
	    Scanner	sc=new Scanner(System.in);
	    System.out.println("Customize timesets for courses ? (y/n)");
	    char opt=Character.toUpperCase(sc.next().charAt(0));
	    int id=-1,sets;
	    boolean done=false;
	    if(opt=='Y')
	    {
	    	while(!done)
	    	{
	    		printOptions(0);
	    	    opt=Character.toUpperCase(sc.next().charAt(0));
	    	    switch(opt)
	    	    {
	    	    	case 'S':printOptions(1);
	    	    	         try{id=Integer.parseInt(sc.next());}
	    	    	         catch(NumberFormatException e)
	    	    	         {
	    	    	         	System.err.println("\nExpected Integer value,");
	    	    	         	id=-1;
	    	    	         }
	    	    	         if(id>=0 && id<courses.length)CID=id;
	    	    	         else printOptions(-1);
	    	    	         break;
	    	    	case 'K':printOptions(3);
	    	    	         if(CID==-1 || sch.src[CID]==null)break;
	    	    	         try
	    	    	         {
	    	    	         	sets=0;
	    	    	         	id=0;
	    	    	         	crcN=new Course(sch.src[CID].code,sch.src[CID].name,sch.src[CID].desc,sch.src[CID].breadth,sch.src[CID].priority);
	    	    	         	while(true)
	    	    	         	{
	    	    	         		id=Integer.parseInt(sc.next());
	    	    	         		if(id==-1)break;
	    	    	         		tmp1=sch.src[CID].src;
		                            while(tmp1!=null)
		                            {
		                            	if(tmp1.ID==id)
		                            	{
		                            		Course.addSet(crcN,tmp1.data);
		                            		sets++;
		                            		break;
		                            	}
		                            	tmp1=tmp1.next;
		                            }
		                            if(tmp1==null)printOptions(4);
	    	    	         	}
	    	    	         	if(sets<=1)crcN.priority=-1;
	    	    	         	sch.src[CID]=crcN;
	    	    	         }
	    	    	         catch(InputMismatchException e)
	    	    	         {
	    	    	         	System.err.println("\nExpected Integer value,");
	    	    	         	printOptions(-1);
	    	    	         }
	    	    	         printOptions(5);
	    	    	         break;
	    	    	case 'R':printOptions(2);
	    	    	         if(CID==-1 || sch.src[CID]==null)break;
	    	    	         try
	    	    	         {
	    	    	         	id=0;
	    	    	         	while(true)
	    	    	         	{
	    	    	         		id=Integer.parseInt(sc.next());
	    	    	         		if(id==-1)break;
	    	    	         		tmp1=sch.src[CID].src;
	    	    	         		if(tmp1.ID==id)sch.src[CID].src=sch.src[CID].src.next;
	    	    	         		else
	    	    	         		{
	    	    	         			while(tmp1.next!=null)
		                                {
		                                	if(tmp1.next.ID==id)
		                                	{
		                                		tmp1.next=tmp1.next.next;
		                                		id=-2;
		                                		break;
		                                	}
		                                	tmp1=tmp1.next;
		                                }
	    	    	         		}
		                            if(tmp1.next==null && id!=-2)printOptions(4);
	    	    	         	}
	    	    	         }
	    	    	         catch(InputMismatchException e)
	    	    	         {
	    	    	         	System.err.println("\nExpected Integer value,");
	    	    	         	printOptions(-1);
	    	    	         }
	    	    	         break;
	    	    	case 'D':System.out.println();
	    	    	         if(CID!=-1)System.out.println(sch.src[CID]);
	    	    	         else printOptions(2);
	    	    	         System.out.println();
	    	    	         break;
	    	    	case 'L':System.out.println();
	    	    	         Schedule.printCourses(sch,false);
	    	    	         System.out.println();
	    	    	         break;
	    	    	case 'M':done=true;
	    	    	         break;
	    	    	case 'Q':System.exit(0);
	    	    	         break;         
	    	    	default:System.out.println("\nInvalid menu option.\n");
	    	    	        break;
	    	    }
	    	}
	    }
	    sc.close();
	    if(sch.makeSchedule())System.out.println(sch);
	    else System.out.println("Schedule doesn't exist.");
	}
	private static void printOptions(int menu)
	{
		if(menu==0)System.out.println("\nSelect course to edit (S).\nSelect timesets to keep (K).\nSelect timesets to remove (R).\nPrint selected course data (D).\nPrint course list (L).\nMake schedule (M).\nExit (Q).\nCurrent selected course : "+((CID==-1 || sch.src[CID]==null)?"null":sch.src[CID].code)+"\n");
		else if(menu==1)System.out.println("\nEnter course ID to select : (-1 to stop)\n");
		else if(menu>1 && (CID==-1 || sch.src[CID]==null))System.out.println("\nYou need to select a valid existing course first ! Back to main menu.\n");
		else if(menu==2)System.out.println("\nEnter timeset IDs for removal : (-1 to stop)\n");
		else if(menu==3)System.out.println("\nEnter timeset IDs for keeping : (-1 to stop)\n");
		else if(menu==4)System.out.println("\nTimeset ID not found, continuing..\n");
		else if(menu==5)System.out.println("\nNote that timeset IDs of timesets will change, which is NOT an error.\n");
		else System.out.println("\nBack to main menu. No changes made.\n");
	}
}
class Schedule
{
	private static String schedule[][],print,tmp,target,listC,nineRep=" |         | ",nineSpc="            ",nineRepS=" |'''''''''| ",nineRepE=" |.........| ",nineRepC="|~~~~~~~~~| ";
	private static int chr,ind,sets,plc,c,until,cfl,maxTime,minTime,dayInd;
	private static long timeTaken;
	private static Node<TimeSet> set;
	private static Node<TimeStamp> tmp3,tmp4;
	private static Node<Integer> node;
	private static TimeStamp stmp;
	private static InputStream str;
	private static Course tmpC;
	private static boolean cont=true;
	int[] dayPrefn=new int[7], dayPrefnLive=new int[7], favTimes, priorities;
	String[] crcs;
	Node<TimeSet>[] soln;
	Course[] src;
	Schedule(String[] crcs, int[] favTimes, int[] priorities)
	{
		this.crcs=crcs;
		this.favTimes=favTimes;
		this.priorities=priorities;
		soln=(Node<TimeSet>[])Array.newInstance(Node.class,crcs.length);
		src=new Course[crcs.length];
	}
	private static boolean updateSelection()
	{
		if((until=tmp.indexOf('\"',ind+1)+1)!=0 && (ind=tmp.indexOf('\"',until))!=-1)
		{
            target=tmp.substring(until,ind);
			return true;
		}
		return false;
	}
	private static String makeDisplayReady(String s)
	{
		for(int i=0;i<s.length();i+=140)
		{
			if(i+140<s.length()-1)
			{
				plc=i+140;
				while(s.charAt(plc)!=' ')plc--;
			    s=s.substring(0,plc)+"\n"+s.substring(plc+1);
			}
			else break;
		}
		return s;
	}
	public static void printCourses(Schedule sch, boolean ext)
	{
		if(!ext)
		{
			for(int i=0;i<sch.crcs.length;i++)
			{
				if(sch.src[i]!=null)System.out.println("Course : "+sch.src[i].code+" ID : "+i);
				else System.out.println("Uninitialized course ID : "+i);
			}
		}
		else
		{
			for(int i=0;i<sch.crcs.length;i++)
		    {
		    	if(sch.src[i]==null)System.out.println("Uninitialized course ID : "+i);
		    	else
		    	{
		    		System.out.println("Course ID : "+i);
			        System.out.println(sch.src[i]);
		    	}
	    	}
		}
	}
	public boolean getCourseData()
	{
		for(int i=0;i<crcs.length;i++)
		{
			try
		    {
                str=new URL("https://timetable.iit.artsci.utoronto.ca/api/20219/courses?code="+crcs[i].substring(0,crcs[i].length()-1)+"&section="+Character.toUpperCase(crcs[i].charAt(crcs[i].length()-1))).openConnection().getInputStream();  
                tmp="";
                timeTaken=System.currentTimeMillis();
                while((chr=str.read())!=-1)tmp+=(char)chr;
                timeTaken=System.currentTimeMillis()-timeTaken;
                str.close();
                ind=-1;
                sets=0;
                while(updateSelection())
                {
                	switch(target)
                	{
                		case "code":updateSelection();
                		            src[i].code=target;
                		            break;
                		case "courseTitle":updateSelection();
                		                   src[i]=new Course();
                		                   src[i].name=target;
                		                   break;
                		case "courseDescription":updateSelection();
                		                         src[i].desc=makeDisplayReady(target.substring(3,target.length()-5));
                		                         break;
                		case "breadthCategories":updateSelection();
                		                         src[i].breadth=target;
                		                         break;
                		case "meetingDay":updateSelection();
                		                  if("MO,TU,WE,TH,FR,SA,SU".indexOf(target)==-1)break;
                		                  stmp=new TimeStamp();
                		        		  stmp.day="MO,TU,WE,TH,FR,SA,SU".indexOf(target)/3;
                		                  break;
                		case "meetingStartTime":updateSelection();
                		                        try{stmp.startTime=Integer.parseInt(target.substring(0,2));}
                		                        catch(NumberFormatException e){}
                		                        break;
                		case "meetingEndTime":updateSelection();
                		                      try
                		                      {
                		                        stmp.endTime=Integer.parseInt(target.substring(0,2));
                		                        TimeSet.addStamp(set.data,stmp);
                		                      }
                		                      catch(NumberFormatException e){}
                		                      break;
                		default:if(target.length()>=4 && target.substring(0,4).equals("LEC-"))
                		        {
                		        	set=Course.addSet(src[i],new TimeSet());
                		        	set.data.lec=target.substring(4);
                		        	sets++;
                		        }
                		        else if(target.length()>=4 && target.substring(0,4).equals("TUT-"))tmp="";
                		        break;
                	}
                }
                if(src[i]!=null)
                {
                	set=src[i].src;
                	if(set.data.src==null && !set.data.lec.substring(0,2).equals("99"))src[i].src=src[i].src.next;
                	while(set.next!=null)
                	{
                		if(set.next.data.src==null && !set.next.data.lec.substring(0,2).equals("99"))set.next=set.next.next;
                		set=set.next;
                	}
                	if(sets<=1)src[i].priority=-1;
                	else src[i].priority=priorities[i];
                }
                System.out.println("Retrieved data for course "+crcs[i]+" successfully in "+(timeTaken/1000.0f)+" seconds ("+(i+1)+" of "+crcs.length+").");
            }
            catch(Exception e)
            {
            	System.err.println("Failed to retrieve course information from server.");
            	return false;
            }
		}
		for(int i=0;i<crcs.length-1;i++)
		{
			if(src[i]==null)continue;
			c=i;
			for(int j=i+1;j<crcs.length;j++)
			{
			    if(src[j]==null)continue;
				if(src[j].priority<src[c].priority)c=j;
			}
			tmpC=src[i];
			src[i]=src[c];
			src[c]=tmpC;
		}
		printCourses(this,true);
		return true;
	}
	private boolean addCourse(int ind, int maxScore, int minPriority, Node<Integer> antiList)
	{
		if(ind==soln.length)return true;
		if(soln[ind]!=null || src[ind]==null)return addCourse(ind+1,Integer.MAX_VALUE,-2,null);
		if(src[ind].priority==-1)
		{
			if(!antiListCheck(src[ind].src.ID,antiList) || this.conflictExistsAt(src[ind].src.data)!=-1)return false;
	   		soln[ind]=src[ind].src;
	   		updateDayPrefn(soln[ind].data,1);
	   		if(cont)return addCourse(ind+1,Integer.MAX_VALUE,-2,null);
	   		else 
	   		{
	   			cont=true;
	   			return true;
	   		}
		}
		Node<TimeSet> max=null;
		int minPI=-1;
		set=src[ind].src;
		while(set!=null)
		{
			cfl=this.conflictExistsAt(set.data);
	   		if(cfl==-1)
	   		{
	   			set.data.score=0;
	   			tmp3=set.data.src;
	   			while(tmp3!=null)
	   			{
	   				for(int k=0;k<favTimes.length;k++)set.data.score+=Math.abs(12-Math.abs(favTimes[k]-tmp3.data.startTime));
	        		set.data.score+=dayPrefnLive[tmp3.data.day]--;
	   				tmp3=tmp3.next;
	   			}
	        	if(set.data.size!=0)set.data.score/=set.data.size;
	        	if(antiListCheck(set.ID,antiList) && set.data.score<maxScore && (max==null || (set.data.score>max.data.score)))max=set;
	        	dayPrefnLive=dayPrefn.clone();
	   		}
	   		else if(src[cfl].priority>minPriority && (minPI==-1 || src[cfl].priority<src[minPI].priority))minPI=cfl;
			set=set.next;
		}
	   	if(max!=null)
	   	{
	   		soln[ind]=max;
	   		updateDayPrefn(soln[ind].data,1);
	   		if(cont && !addCourse(ind+1,Integer.MAX_VALUE,-2,null))
	   		{
	   			updateDayPrefn(soln[ind].data,-1);
	   			soln[ind]=null;
	   			return addCourse(ind,max.data.score,minPriority,antiList);
	   		}
	   		cont=true;
	   		return true;
	   	}
	   	if(minPI==-1)return false;
		if(antiList==null)antiList=new Node<Integer>(soln[minPI].ID);
		else
		{
			node=antiList;
			while(node.next!=null)node=node.next;
			node.next=new Node<Integer>(soln[minPI].ID);
		}
		updateDayPrefn(soln[minPI].data,-1);
	   	Node<TimeSet> backup=soln[minPI];
	   	soln[minPI]=null;
	   	cont=false;
	   	if(!addCourse(minPI,Integer.MAX_VALUE,-2,antiList)) 
	   	{
	   		soln[minPI]=backup;
	   		updateDayPrefn(soln[minPI].data,1);
	   		return addCourse(ind,maxScore,src[minPI].priority,antiList);
	   	}
	   	return addCourse(ind,maxScore,minPriority,antiList);
	}
	public boolean makeSchedule()
	{
		boolean success=addCourse(0,Integer.MAX_VALUE,-2,null);
		if(success)mergeSolution();
		return success;
	}
	private void mergeSolution()
	{
		minTime=Integer.MAX_VALUE;
		maxTime=-1;
		listC="";
		for(int i=soln.length-1;i>=0;i--)
		{
			if(soln[i]==null || soln[i].data.src==null)continue;
	   	    if(soln[i].data.src.data.startTime<minTime)minTime=soln[i].data.src.data.startTime;
	   	   	if(soln[i].data.maxTime>maxTime)maxTime=soln[i].data.maxTime;
		}
		schedule=new String[maxTime-minTime+2][14];
		for(int i=0;i<soln.length;i++)
		{
			if(soln[i]==null)continue;
	        tmp=src[i].code+"-"+soln[i].data.lec.substring(0,2);
	        listC+=tmp+", ";
	        if(soln[i].data.src==null)continue;
	        tmp4=soln[i].data.src;
		    while(tmp4!=null)
            {
            	dayInd=tmp4.data.day << 1;
            	for(int k=tmp4.data.startTime-minTime;k<=tmp4.data.endTime-minTime;k++)
	    		{
	    			if(schedule[k][dayInd]==null)
	    			{
	    				schedule[k][dayInd]=tmp;
	    			    schedule[k][1+dayInd]=getRepresentator(k+minTime,tmp4.data);
	    			}
	    			else
	    			{
	    				schedule[k][dayInd]=schedule[k][dayInd].substring(0,3)+" - "+src[i].code.substring(0,3)+"   ";
	    				schedule[k][1+dayInd]=nineRepC;
	    			}
	    		}
		        tmp4=tmp4.next;
		    }
		}
		listC=listC.substring(0,listC.length()-2);
		maxTime=schedule.length-1;
		schedule[maxTime][1]="  MONDAY  ";
		schedule[maxTime][3]="   TUESDAY  ";
		schedule[maxTime][5]="  WEDNESDAY";
		schedule[maxTime][7]="   THURSDAY ";
		schedule[maxTime][9]="    FRIDAY  ";
		schedule[maxTime][11]="   SATURDAY ";
		schedule[maxTime][13]="    SUNDAY";
	}
	public String toString()
    {
    	tmp="";
    	for(int i=0;i<favTimes.length;i++)tmp+=favTimes[i]+", ";
    	print="Favoured times : "+tmp.substring(0,tmp.length()-2)+".\n\nSchedule :-\n\t  ";
		maxTime=schedule.length-1;
    	for(int i=0;i<14;i++)print+=schedule[maxTime][i]==null?nineSpc:schedule[maxTime][i];
    	print+="\n\n";
    	for(int i=0;i<schedule.length-1;i++)
    	{
    		print+=(i+minTime<=9?" 0":" ")+(i+minTime)+":00 : ";
    		for(int j=0;j<schedule[i].length;j++)print+=schedule[i][j]==null?nineSpc:schedule[i][j];
    	    print+="\n\n";
    	}
    	print+="List of courses used : "+listC+".";
    	return print;
    }
    private static String getRepresentator(int curTime, TimeStamp t)
    {
    	if(t.startTime==curTime)return nineRepS;
    	else if(t.endTime==curTime)return nineRepE;
    	return nineRep;
    }
	public int conflictExistsAt(TimeSet t)
	{
		if(t==null)return -1;
		tmp3=t.src;
		while(tmp3!=null)
	   	{
	   		for(int i=soln.length-1;i>=0;i--)
	   	    {
	   	    	if(soln[i]==null)continue;
	   	    	tmp4=soln[i].data.src;
		        while(tmp4!=null)
		        {
		        	if(TimeStamp.isOverlapping(tmp4.data,tmp3.data))return i;
		        	tmp4=tmp4.next;
		        }
	   	    }
	   	    tmp3=tmp3.next;
	   	}
	   	return -1;
	}
	private static boolean antiListCheck(int ind, Node<Integer> src)
	{
		node=src;
		while(node!=null)
		{
			if(node.data==ind)return false;
			node=node.next;
		}
		return true;
	}
	private void updateDayPrefn(TimeSet t, int sign)
	{
		if(t==null)return;
		tmp3=t.src;
		while(tmp3!=null)
		{
			dayPrefn[tmp3.data.day]-=sign;
			tmp3=tmp3.next;
		}
		dayPrefnLive=dayPrefn.clone();
	}
}
class Course
{
	Node<TimeSet> src;
    String name,desc,code,breadth;
    int priority;
    private static Node<TimeSet> tmp1;
    private static Node<TimeStamp> tmp2;
    Course(){}
    Course(String code, String name, String desc, String breadth, int priority)
    {
    	this.code=code;
    	this.name=name;
    	this.desc=desc;
    	this.breadth=breadth;
    	this.priority=priority;
    }
    public static Node<TimeSet> addSet(Course to, TimeSet t)
	{
		if(to.src==null)
		{
			to.src=new Node<TimeSet>(t);
			return to.src;
		}
		else
		{
			tmp1=to.src;
			while(tmp1.next!=null)tmp1=tmp1.next;
			tmp1.next=new Node<TimeSet>(t);
			return tmp1.next;
		}
	}
    private static String print,tmp,nineRep="|       |\t",nineSpc="         \t",nineRepS="|'''''''|\t",nineRepE="|.......|\t",nineRepC="|~~~~~~~|\t";
    public String toString()
    {
    	print="Course name : "+name+" ("+code+").\nPriority level : "+priority+".\nBreadth Category : "+breadth+".\nDescription :-\n"+desc+"\n";
    	tmp1=src;
    	while(tmp1!=null)
    	{
    		if(tmp1.data.src==null)
    		{
    			print+="Schedule for lecture set \'"+tmp1.data.lec+"\' is undefined, ID : "+tmp1.ID+"\n";
    			tmp1=tmp1.next;
    			continue;
    		}
    		print+="Schedule for lecture set \'"+tmp1.data.lec+"\', ID : "+tmp1.ID+" :-\n\t\t  MONDAY  \t TUESDAY \tWEDNESDAY\tTHURSDAY \t FRIDAY  \tSATURDAY \t SUNDAY\n\n";
    		for(int j=tmp1.data.src.data.startTime;j<=tmp1.data.maxTime;j++)
    		{
    			print+=(j<=9?"0":"")+j+":00 :";
    			tmp="";
    			tmp2=tmp1.data.src;
    			while(tmp2!=null)
    			{
    				if(tmp2.data.startTime>j)break;
    				if(tmp2.data.endTime>=j)
    				{
    					if(tmp2.data.day<tmp.length()/10)tmp=tmp.substring(0,10*tmp2.data.day)+getRepresentator(j,tmp2.data)+tmp.substring(tmp2.data.day*10+10);
    					else
    					{
                            for(int l=tmp.length()/10;l<tmp2.data.day;l++)tmp+=nineSpc;
    					    tmp+=getRepresentator(j,tmp2.data);
    					}
    				}
    				tmp2=tmp2.next;
    			}
    			print+="\t\t"+tmp+"\n\n";
    		}
    		tmp1=tmp1.next;
    	}
    	return print;
    }
    private static String getRepresentator(int curTime, TimeStamp t)
    {
    	if(t.startTime==curTime)return nineRepS;
    	else if(t.endTime==curTime)return nineRepE;
    	return nineRep;
    }
}
class TimeSet
{
	Node<TimeStamp> src;
	String lec;
	int score,maxTime=-1,size=0;
    private static Node<TimeStamp> tmp1,tmp2;
    TimeSet(){}
	TimeSet(String lec)
	{
		this.lec=lec;
	}
	public static boolean isConsistent(TimeSet t)
	{
		tmp1=t.src;
		while(tmp1!=null)
		{
			tmp2=tmp1.next;
			while(tmp2!=null)
			{
				if(TimeStamp.isOverlapping(tmp1.data,tmp2.data))return false;
				tmp2=tmp2.next;
			}
			tmp1=tmp1.next;
		}
		return true;
	}
	public static void addStamp(TimeSet to, TimeStamp t)
	{
		to.size++;
		if(to.maxTime<t.endTime)to.maxTime=t.endTime;
		if(to.src==null)to.src=new Node<TimeStamp>(t);
		else
		{
			tmp1=to.src;
			tmp2=to.src.next;
			if(tmp1.data.startTime<t.startTime || (tmp1.data.startTime==t.startTime && tmp1.data.day<t.day))
			{
				while(tmp2!=null)
			    {
			    	if(tmp2.data.startTime<t.startTime || (tmp2.data.startTime==t.startTime && tmp2.data.day<t.day))
			    	{
			    		tmp1=tmp2;
			    		tmp2=tmp2.next;
			    	}
			    	else add(tmp1,t);
			    }
			    add(tmp1,t);
			}
			else
			{
				to.src=new Node<TimeStamp>(t);
				to.src.next=tmp1;
			}
		}
	}
	private static void add(Node<TimeStamp> to, TimeStamp t)
	{
		if(to.next==null)to.next=new Node<TimeStamp>(t);
		else
		{
			tmp2=to.next;
		    to.next=new Node<TimeStamp>(t);
		    to.next.next=tmp2;
		}
	}
}
class TimeStamp
{
    int day,startTime,endTime;
    TimeStamp(){}
    TimeStamp(int day, int startTime, int endTime)
    {
    	this.day=day;
    	this.startTime=startTime;
    	this.endTime=endTime;
    }
    public static boolean isOverlapping(TimeStamp a, TimeStamp b)
    {
    	if(a.day!=b.day)return false;
    	if(a.startTime==b.startTime)return true;
    	if(a.startTime>b.startTime)
    	{
    		if(b.endTime<=a.startTime)return false;
    		return true;
    	}
    	else
    	{
    		if(a.endTime<=b.startTime)return false;
    		return true;
    	}
    }
}
class Node<T>
{
	T data;
	int ID;
	Node<T> next;
    private static int count=1;
    Node()
    {
    	this.ID=count++;
    }
	Node(T value)
	{
		this.data=value;
		this.ID=count++;
	}
}