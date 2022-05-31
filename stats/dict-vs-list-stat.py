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

def get_list() -> Tuple[Tuple[Tuple[List[int]]], List[int], List[int]]:
    lst = (([], []), ([], []), ([], []), ([], []), ([], []), ([], []), ([], []))
    to_rem_lec = []
    to_rem_tut = []
    for i in range(7):
        for _ in range(5):
            lst[i][0].append(random.randint(1 << 35, 1 << 40))
            lst[i][1].append(random.randint(1 << 35, 1 << 40))
        to_rem_lec.append(lst[i][0][2])
        to_rem_tut.append(lst[i][1][2])
    return (lst, to_rem_lec, to_rem_tut)

def list_remove_lecs(lst, to_rem_lec, to_rem_tut) -> None:
    for i in range(7):
        lst[i][0].remove(to_rem_lec[i])
        lst[i][1].remove(to_rem_tut[i])

def dict_remove_lecs(lst, to_rem_lec, to_rem_tut) -> None:
    for i in range(7):
        del lst[i][0][to_rem_lec[i]]
        del lst[i][1][to_rem_tut[i]]

if __name__ == '__main__':
    # proves del dict[key] better than list.remove()
    runs = 10000
    list_rem_time = 0
    dict_rem_time = 0
    for _ in range(runs):
        lst, to_rem_lec, to_rem_tut = get_list()
        start = time.time()
        list_remove_lecs(lst, to_rem_lec, to_rem_tut)
        list_rem_time += time.time() - start
        lst, to_rem_lec, to_rem_tut = get_dict()
        start = time.time()
        dict_remove_lecs(lst, to_rem_lec, to_rem_tut)
        dict_rem_time += time.time() - start
    list_rem_time /= runs
    dict_rem_time /= runs
    print(list_rem_time, dict_rem_time)