from typing import *
import time
import random

def get_dict() -> Tuple[Tuple[Tuple[List[int]]], List[int], List[int]]:
    lst = (({}, {}), ({}, {}), ({}, {}), ({}, {}), ({}, {}), ({}, {}), ({}, {}))
    to_rem_lec = []
    to_rem_tut = []
    for i in range(7):
        for _ in range(5):
            lst[i][0][random.randint(1 << 35, 1 << 40)] = {"a":1, "b":2, "c":3}
            lst[i][1][random.randint(1 << 35, 1 << 40)] = {"a":1, "b":2, "c":3}
        to_rem_lec.append(list(lst[i][0].keys())[2])
        to_rem_tut.append(list(lst[i][1].keys())[2])
    return (lst, to_rem_lec, to_rem_tut)

def remove_lecs(lst, to_rem_lec, to_rem_tut) -> None:
    for i in range(7):
        del lst[i][0][to_rem_lec[i]]
        del lst[i][1][to_rem_tut[i]]

def edit_lecs(lst, to_rem_lec, to_rem_tut) -> None:
    for i in range(7):
        lst[i][0][to_rem_lec[i]]['c'] += 5
        lst[i][1][to_rem_tut[i]]['c'] += 5

if __name__ == '__main__':
    # proves del dict[key] better than phantom flag implementation
    runs = 10000
    rem_time = 0
    edit_time = 0
    for _ in range(runs):
        lst, to_rem_lec, to_rem_tut = get_dict()
        start = time.time()
        edit_lecs(lst, to_rem_lec, to_rem_tut)
        edit_time += time.time() - start
        lst, to_rem_lec, to_rem_tut = get_dict()
        start = time.time()
        remove_lecs(lst, to_rem_lec, to_rem_tut)
        rem_time += time.time() - start
    rem_time /= runs
    edit_time /= runs
    print(rem_time, edit_time)