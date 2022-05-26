Python based optimal scheduler, handles eveything given a valid set of courses.

In main(), editable variables:

1) crcs : courses you want to add to your schedule. must specify session (F / S / Y) or add 'A' for all.
2) allow_async : allow_aync[i] for crcs[i]; setting it as True itself implies all allowed, and False implies all not allowed.
3) timePrefnsFall : fall time preferences in 24hr format.
4) timePrefnsWinter : winter time preferences in 24hr format.
5) balanced : True if balanced work load wanted in the week.
6) weights : recommended to not touch, but for experimentation, [time_score_weight, week_score_weight].
7) crcPrefns : all courses with session (see below for 'A' type) in descending priority.
8) '2021' at line 989 with year to read data from; removing implies current year.

global editable variables:

1) PRECISION : float output precision.

It is advised that you check the course sessions first, and modify the values correctly.

'A' flag will read all sessions, and you must specify the relative priority between all sessions in crcPrefns for the same course.

The program does NOT verify prerequisites, corequisites and exclusions.
