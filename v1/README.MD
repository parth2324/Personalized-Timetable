Python based optimal scheduler with non-competitive scoring system, handles eveything given a valid set of courses.

In main(), editable variables:

1) crcs : courses you want to add to your schedule. must specify session (F / S / Y) or add 'A' for all.
2) timePrefnsFall : fall time preferences in 24hr format.
3) timePrefnsWinter : winter time preferences in 24hr format.
4) balanced : True if balanced work load wanted in the week.
5) crcPrefns : all courses with session (see below for 'A' type) in descending priority.
6) '2021' at line 989 with year to read data from.

It is advised that you check the course sessions first, and modify the values correctly.

'A' flag will read all sessions, and you must specify the relative priority between all sessions in crcPrefns for the same course.

The program does NOT verify prerequisites, corequisites and exclusions.
