from typing import *
import time
import random

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

def remove_lecs(lst, to_rem_lec, to_rem_tut) -> None:
    for i in range(7):
        lst[i][0].remove(to_rem_lec[i])
        lst[i][1].remove(to_rem_tut[i])

def edit_lecs(lst, to_rem_lec, to_rem_tut) -> None:
    for i in range(7):
        for j in range(5):
            if lst[i][0][j] == to_rem_lec[i]:
                lst[i][0][j] += 5
                break
        for j in range(5):
            if lst[i][1][j] == to_rem_tut[i]:
                lst[i][1][j] += 5
                break

if __name__ == '__main__':
    # proves .remove() better than phantom flag implementation
    runs = 100000
    rem_time = 0
    edit_time = 0
    for _ in range(runs):
        lst, to_rem_lec, to_rem_tut = get_list()
        start = time.time()
        edit_lecs(lst, to_rem_lec, to_rem_tut)
        edit_time += time.time() - start
        lst, to_rem_lec, to_rem_tut = get_list()
        start = time.time()
        remove_lecs(lst, to_rem_lec, to_rem_tut)
        rem_time += time.time() - start
    rem_time /= runs
    edit_time /= runs
    print(rem_time, edit_time)