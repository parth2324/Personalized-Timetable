from __future__ import annotations
from typing import *
from json import loads
from urllib.request import urlopen
import threading
import time
import math

# address helpers, must be reset from _init_(), sample:
CRC_MASK   = 0b00000000000000000000000000000000000011111
SESS_MASK  = 0b00000000000000000000000000000000001100000
TYPE_MASK  = 0b00000000000000000000000000000000010000000
LEC_MASK   = 0b00000000000000000000000000001111100000000
ASYNC_MASK = 0b00000000000000000000000000010000000000000
DAY_MASK   = 0b00000000000000000000000011100000000000000
START_MASK = 0b00000000000011111111111100000000000000000
END_MASK   = 0b11111111111100000000000000000000000000000
CLEAN_MASK = 0b00000000000000000000000000011111111111111
CRC_MASK_SIZE = 5
LEC_MASK_SIZE = 5
MAX_PRIORITY = 1 << (CRC_MASK_SIZE + 1)
SESS_SHFT = 5
TYPE_SHFT = 7
LEC_SHFT = 8
ASYNC_SHFT = 13
DAY_SHFT = 14
START_SHFT = 17
END_SHFT = 29

# keys
MEETINGS = 'meetings'
SCHEDULE = 'schedule'
TYPE = 'teachingMethod'
MODE = 'deliveryMode'
CANCEL = 'cancel'
START = 'meetingStartTime'
END = 'meetingEndTime'
DAY = 'meetingDay'
TUTORIALS = 'tutorials'
HAS_TUT = 'hasTutorial'
ASYNC = 'isAsynchronous'
LEN = 'size'
TSCORE = 'timeScore'
ID = 'indexing'
S = 'S'
F = 'F'
Y = 'Y'

# maps
TYPE_MAP = {MEETINGS: 0, TUTORIALS: 1}
TYPE_MAP_R = [MEETINGS, TUTORIALS]
SESS_MAP = {F: 0, S: 1, Y: 2}
SESS_MAP_R = [F, S, Y]
ASYNC_MAP = {False: 0, True: 1}
ASYNC_MAP_R = [False, True]

# common data
DAYS_LONG = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DAYS_SHORT = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
RANGE_SEVEN = [0, 1, 2, 3, 4, 5, 6]
STATE_PLACE_HOLDER = [0, 0, [0, 0, 0]]
STATE_ITERATOR_PLACE_HOLDER = [[0, 0, [0, 0, 0]]]
NEW_STATE_ITERATOR_PLACE_HOLDER = [None]
SLEEP = 0.001
TRUE = True

# -- editable begin --

PRECISION = 3

# -- editable end --

class Scheduler:
    # LEC_TUT_CONFLICT_POLICY = LEC_OVER_TUT
    # TODO: add greedy mode (estimated score range based)
    data: Dict
    _initialized: bool
    _priority_map: Dict[str, Dict[str, int]]
    _week_weight: float
    _week_balance_invert: int
    _state: Tuple[Tuple, Tuple, List]

    def __init__(self, crcs: List[str], allow_async: Union[List[bool], bool] = True, year: int = time.strptime(time.ctime()).tm_year) -> None:
        self.data = {ID: []}
        self._initialized = False
        self._priority_map = {}
        self._week_weight = -1
        self._week_balance_invert = -1
        self._state = ((([], []), ([], []), ([], []), ([], []), ([], []), ([], []), ([], [])), # fall_schedule : day -> type -> crcs
                       (([], []), ([], []), ([], []), ([], []), ([], []), ([], []), ([], [])), # winter_schedule
                       [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], 0, 0, 0], ([], [])) # [fall_week_load, winter_weekload, state_score, #fall_crcs, #winter_crcs], (async_fall_crcs, async_winter_crcs)
        workers = []
        i = 0
        if  isinstance(allow_async, bool):
            for crc in crcs:
                workers.append(threading.Thread(target=self._read_data, args=(crc, year, i, not allow_async), daemon=True))
                i += 1
        else:
            for crc in crcs:
                workers.append(threading.Thread(target=self._read_data, args=(crc, year, i, not allow_async[i]), daemon=True))
                i += 1
        threading.Thread(target=self._init_, args=(workers, ), daemon=True).start()

    def _init_(self, workers: List[threading.Thread]) -> None:
        global MAX_PRIORITY, LEC_MASK_SIZE, CRC_MASK_SIZE, CRC_MASK, SESS_MASK, SESS_SHFT, LEC_MASK, LEC_SHFT, TYPE_MASK, TYPE_SHFT, ASYNC_MASK, ASYNC_SHFT, DAY_MASK, DAY_SHFT, START_MASK, START_SHFT, END_MASK, END_SHFT, CLEAN_MASK
        print(f'starting scheduler initialization..')
        start_time = time.time()
        for worker in workers:
            worker.start()
        i = 0
        while i < len(workers):
            if workers[i].is_alive():
                time.sleep(SLEEP)
            else:
                i += 1
        self._initialized = True
        CRC_MASK_SIZE, LEC_MASK_SIZE = self.get_address_size()
        MAX_PRIORITY = 1 << (CRC_MASK_SIZE + 1)
        CRC_MASK = (1 << CRC_MASK_SIZE) - 1
        SESS_SHFT = CRC_MASK_SIZE
        SESS_MASK = (1 << (SESS_SHFT + 2)) - (1 << SESS_SHFT)
        TYPE_SHFT = SESS_SHFT + 2
        TYPE_MASK = (1 << (TYPE_SHFT + 1)) - (1 << TYPE_SHFT)
        LEC_SHFT = TYPE_SHFT + 1
        LEC_MASK = (1 << (LEC_SHFT + LEC_MASK_SIZE)) - (1 << LEC_SHFT)
        ASYNC_SHFT = LEC_SHFT + LEC_MASK_SIZE
        ASYNC_MASK = (1 << (ASYNC_SHFT + 1)) - (1 << ASYNC_SHFT)
        DAY_SHFT = ASYNC_SHFT + 1
        DAY_MASK = (1 << (DAY_SHFT + 3)) - (1 << DAY_SHFT)
        START_SHFT = DAY_SHFT + 3
        START_MASK = (1 << (START_SHFT + 12)) - (1 << START_SHFT)
        END_SHFT = START_SHFT + 12
        END_MASK = (1 << (END_SHFT + 12)) - (1 << END_SHFT)
        CLEAN_MASK = CRC_MASK + SESS_MASK + TYPE_MASK + LEC_MASK + ASYNC_MASK
        print(f"COURSE_MASK_SIZE: {CRC_MASK_SIZE} bits -> {bin(CRC_MASK)}")
        print(f"SESSION_MASK_SIZE: 2 bits -> {bin(SESS_MASK)}")
        print(f"TYPE_MASK_SIZE: 1 bit -> {bin(TYPE_MASK)}")
        print(f"LECTURE_MASK_SIZE: {LEC_MASK_SIZE} bits -> {bin(LEC_MASK)}")
        print(f"ASYNC_MASK_SIZE: 1 bit -> {bin(ASYNC_MASK)}")
        print(f"DAY_MASK_SIZE: 3 bits -> {bin(DAY_MASK)}")
        print(f"START_MASK_SIZE: 12 bits -> {bin(START_MASK)}")
        print(f"END_MASK_SIZE: 12 bits -> {bin(END_MASK)}")
        print(f"CLEAN_MASK_SIZE: {CRC_MASK_SIZE + 2 + 1 + LEC_MASK_SIZE + 1} bits -> {bin(CLEAN_MASK)}")
        print(f"ADDRESS_SIZE: {CRC_MASK_SIZE + 2 + 1 + LEC_MASK_SIZE + 1 + 3 + 12 + 12} bits")
        print(f'initialized scheduler in {round(time.time() - start_time, PRECISION)} seconds.')

    def _read_data(self, crc: str, year: int, id: int, not_allow_async: bool = True) -> None:
        sect = crc[len(crc) - 1].upper()
        if sect == 'A': # equaivalent to any, can take both!
            sect = ''
        crc = crc[0:len(crc) - 1]
        self.data[ID].append(crc)
        self.data[crc] = {}
        self.data[crc][ID] = id
        print(f'reading {crc} data from server..')
        start_time = time.time()
        buffer = loads(urlopen(f'https://timetable.iit.artsci.utoronto.ca/api/{year}9/courses?code={crc}&section={sect}&available=t').read())
        print(f'read {crc} data from server in {round(time.time() - start_time, PRECISION)} seconds.')
        print(f'detecting, cleaning and integerizing lectures for {crc}..')
        start_time = time.time()
        # NOTE: maximum total iterations ~ 700:
        # NOTE: ASYNC_SCORE_POLICY = MAX_TSCORE
        for key in buffer:
            self.data[crc][key[9]] = buffer[key]
            sect_data = self.data[crc][key[9]]
            sect_data[TUTORIALS] = {}
            sect_data[HAS_TUT] = False
            lec_to_del = []
            for lec in sect_data[MEETINGS]:
                lec_data = sect_data[MEETINGS][lec]
                if lec_data[CANCEL] == 'Cancelled':
                    lec_to_del.append(lec)
                    continue
                if lec_data[MODE] == 'ONLASYNC':
                    if not_allow_async:
                        lec_to_del.append(lec)
                        continue
                    lec_data[ASYNC] = True
                    for stmp in lec_data[SCHEDULE]:
                        lec_data[SCHEDULE][stmp][LEN] = 0
                    if lec_data[TYPE] == 'TUT' or lec_data[TYPE] == 'PRA':
                        sect_data[HAS_TUT] = True
                        sect_data[TUTORIALS][lec] = lec_data
                        lec_to_del.append(lec)
                    continue
                else:
                    lec_data[ASYNC] = False
                for stmp in lec_data[SCHEDULE]:
                    stmp_data = self.data[crc][key[9]][MEETINGS][lec][SCHEDULE][stmp]
                    stmp_data[DAY] = DAYS_SHORT.index(stmp_data[DAY])
                    if stmp_data[START][3:] == '00':
                        stmp_data[START] = int(stmp_data[START][0:2]) * 100
                    else:
                        stmp_data[START] = int(stmp_data[START][0:2] + stmp_data[START][3:])
                    if stmp_data[END][3:] == '00':
                        stmp_data[END] = int(stmp_data[END][0:2]) * 100
                    else:
                        stmp_data[END] = int(stmp_data[END][0:2] + stmp_data[END][3:])
                    stmp_data[LEN] = stmp_data[END] - stmp_data[START]
                if lec_data[TYPE] == 'TUT' or lec_data[TYPE] == 'PRA':
                    sect_data[HAS_TUT] = True
                    sect_data[TUTORIALS][lec] = lec_data
                    lec_to_del.append(lec)
            meet_data = self.data[crc][key[9]][MEETINGS]
            for lec in lec_to_del:
                del meet_data[lec]
            meet_data[ID] = list(meet_data)
            i = 0
            for lec in meet_data[ID]:
                meet_data[lec][ID] = i
                i += 1
            meet_data = self.data[crc][key[9]][TUTORIALS]
            meet_data[ID] = list(meet_data)
            i = 0
            for lec in meet_data[ID]:
                meet_data[lec][ID] = i
                i += 1
        print(f'detected, cleaned and integerized all lectures for {crc} in {round(time.time() - start_time, PRECISION)} seconds.')

    def _init_time_score(self, crc: str, session: str, type: str, prefns: List[int], weight: float) -> None:
        for lec in self.data[crc][session][type][ID]:
            dct = self.data[crc][session][type][lec]
            if dct[ASYNC]:
                dct[TSCORE] = weight * self._priority_map[crc][session] * 1200
                continue
            dct[TSCORE] = 0
            for stmp in dct[SCHEDULE]:
                for prefn in prefns:
                    dct[TSCORE] += abs(1200 - abs(prefn - 0.5 * (dct[SCHEDULE][stmp][START] + dct[SCHEDULE][stmp][END])))
            dct[TSCORE] *= (weight * self._priority_map[crc][session]) / len(dct[SCHEDULE])

    def get_read_courses(self) -> List[str]:
        if not self._initialized:
            print('waiting for initialization to complete for getting read courses..')
            while not self._initialized:
                time.sleep(SLEEP) # init daemons join
        crcs = []
        for crc in self.data[ID]:
            if F in self.data[crc]:
                crcs.append(crc + F)
            if S in self.data[crc]:
                crcs.append(crc + S)
            elif Y in self.data[crc]:
                crcs.append(crc + Y)
        return crcs
    
    def get_address_size(self) -> Tuple(int, int):
        max_size = 0
        for crc in self.data[ID]:
            if F in self.data[crc]:
                max_size = max(len(self.data[crc][F][MEETINGS][ID]), max(len(self.data[crc][F][TUTORIALS][ID]), max_size))
            if S in self.data[crc]:
                max_size = max(len(self.data[crc][S][MEETINGS][ID]), max(len(self.data[crc][S][TUTORIALS][ID]), max_size))
            elif Y in self.data[crc]:
                max_size = max(len(self.data[crc][Y][MEETINGS][ID]), max(len(self.data[crc][Y][TUTORIALS][ID]), max_size))
        return (int(1 + math.floor(math.log2(len(self.data[ID])))), int(1 + math.floor(math.log2(max_size))))

    def _overlaps(self, stmp1: Dict, addr2: int) -> bool:
        if stmp1[DAY] != ((addr2 & DAY_MASK) >> DAY_SHFT):
            return False
        if stmp1[START] > ((addr2 & START_MASK) >> START_SHFT):
            if stmp1[START] < ((addr2 & END_MASK) >> END_SHFT):
                return True
        elif stmp1[END] > ((addr2 & START_MASK) >> START_SHFT):
            return True
        return False

    def make_schedule(self, timePrefnsFall: List[int], timePrefnsWinter: List[int], crcPrefns: List[str], weights: List[float] = [3, 2], balancedWeek: bool = True) -> bool:
        # weights = [TSCORE_WEIGHT, WEEK_WEIGHT]
        # TSCORE(CRC.LEC) = CRC.PRIORITY * TSCORE_WEIGHT * SUM(ABS(1200 - ABS(PREFN - LEC.SCHEDULE.START)))
        if not self._initialized:
            print('waiting for initialization to complete for making schedule..')
            while not self._initialized:
                time.sleep(SLEEP) # init daemons join
        self._week_weight = weights[1]
        if balancedWeek:
            self._week_balance_invert = 1200 * 7
        else:
            self._week_balance_invert = 0
        print('initializing course priority map..')
        start_time = time.time()
        crcPrefns = crcPrefns[:]
        for i in range(len(crcPrefns)):
            sect = crcPrefns[i][len(crcPrefns[i]) - 1].upper()
            crc = crcPrefns[i][0:len(crcPrefns[i]) - 1]
            crcPrefns[i] = crc
            if crc not in self._priority_map:
                self._priority_map[crc] = {}
            self._priority_map[crc][sect] = len(crcPrefns) - i + 1
        crcPrefns = list(dict.fromkeys(crcPrefns))
        print(f'initialized course priority map in {round(time.time() - start_time, PRECISION)} seconds.')
        print('initializing time scores for all lectures..')
        start_time = time.time()
        for crc in crcPrefns:
            if F in self.data[crc]:
                self._init_time_score(crc, F, MEETINGS, timePrefnsFall, weights[0])
                self._init_time_score(crc, F, TUTORIALS, timePrefnsFall, weights[0])
            if S in self.data[crc]:
                self._init_time_score(crc, S, MEETINGS, timePrefnsWinter, weights[0])
                self._init_time_score(crc, S, TUTORIALS, timePrefnsWinter, weights[0])
            elif Y in self.data[crc]:
                self._init_time_score(crc, Y, MEETINGS, timePrefnsFall, weights[0])
                self._init_time_score(crc, Y, TUTORIALS, timePrefnsFall, weights[0])
        print(f'initialized time scores for all lectures in {round(time.time() - start_time, PRECISION)} seconds.')
        print('starting to make schedule..')
        start_time = time.time()
        count = 0.0
        for crc in crcPrefns:
            print(f'percentage complete : {round(100 * (count / len(self.data[ID])), PRECISION)}%')
            print(f'attempting to add {crc} to schedule..')
            crc_time = time.time()
            result = self._add_course(crc, self._state, [], [])
            if result[0] is None:
                print(f'schedule does not exist for given courses, lost {round(time.time() - start_time, PRECISION)} seconds.\nschedule so far :')
                self.print_schedule()
                return False
            self._state = result[0]
            if SESS_MAP_R[(result[1] & SESS_MASK) >> SESS_SHFT] == F:
                self._state[2][3] += 1
            elif SESS_MAP_R[(result[1] & SESS_MASK) >> SESS_SHFT] == S:
                self._state[2][4] += 1
            else:
                self._state[2][3] += 1
                self._state[2][4] += 1
            print(f'added {crc} to schedule in {round(time.time() - crc_time, PRECISION)} seconds.')
            count += 1
        print(f'successfully made a schedule in {round(time.time() - start_time, PRECISION)} seconds.')
        return True

    def _add_course(self, crc: str, state: Tuple[Tuple, Tuple, List], lec_to_ignore: List[int], tut_to_ignore: List[int], do_lec: bool = True, do_tut: bool = True) -> List:    
        winter = S in self.data[crc]
        if winter != (F in self.data[crc]):
            if winter:
                if self.data[crc][S][HAS_TUT] and do_tut:
                    if do_lec:
                        return self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state,
                                                   (self.data[crc][ID] + (5 << SESS_SHFT), None), lec_to_ignore, tut_to_ignore)
                    else:
                        return self._state_iterator_winter(self.data[crc][ID] + (5 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                elif do_lec:
                    return self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
            else:
                if self.data[crc][F][HAS_TUT] and do_tut:
                    if do_lec:
                        return self._state_iterator_fall(self.data[crc][ID], state,
                                                   (self.data[crc][ID] + (1 << TYPE_SHFT), None), lec_to_ignore, tut_to_ignore)
                    else:
                        return self._state_iterator_fall(self.data[crc][ID] + (1 << TYPE_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                elif do_lec:
                    return self._state_iterator_fall(self.data[crc][ID], state, None, lec_to_ignore, tut_to_ignore)
        elif Y in self.data[crc]: # hard iterizable !
            result = NEW_STATE_ITERATOR_PLACE_HOLDER
            new_state = state
            if do_lec:
                to_ignore = lec_to_ignore[:]
                lec_fall = self._state_iterator_fall(self.data[crc][ID] + (2 << SESS_SHFT), state, None, to_ignore, tut_to_ignore)
                if lec_fall[0] is None:
                    return lec_fall
                new_state = self._try_push_winter(lec_fall[1], lec_fall[0], tut_to_ignore, to_ignore[:])
                while new_state is None:
                    to_ignore.append(lec_fall[1])
                    lec_fall = self._state_iterator_fall(self.data[crc][ID] + (2 << SESS_SHFT), state, None, to_ignore, tut_to_ignore)
                    if lec_fall[0] is None:
                        return lec_fall
                    new_state = self._try_push_winter(lec_fall[1], lec_fall[0], tut_to_ignore, to_ignore[:])
                result = [new_state, lec_fall[1]]
            if do_tut:
                to_ignore = tut_to_ignore[:]
                tut_fall = self._state_iterator_fall(self.data[crc][ID] + (6 << SESS_SHFT), new_state, None, lec_to_ignore, to_ignore)
                if tut_fall[0] is None:
                    return tut_fall
                new_state_ = self._try_push_winter(tut_fall[1], tut_fall[0], to_ignore, lec_to_ignore[:])
                while new_state_ is None:
                    to_ignore.append(tut_fall[1])
                    tut_fall = self._state_iterator_fall(self.data[crc][ID] + (6 << SESS_SHFT), new_state, None, lec_to_ignore, to_ignore)
                    if tut_fall[0] is None:
                        return tut_fall
                    new_state_ = self._try_push_winter(tut_fall[1], tut_fall[0], to_ignore, lec_to_ignore[:])
                if result[0] == None:
                    result = [new_state_, tut_fall[1]]
                else:
                    result[0] = new_state_
                    result.insert(1, tut_fall[1])
            return result
        else: # session = 'A'
            result_fall = NEW_STATE_ITERATOR_PLACE_HOLDER
            result_winter = NEW_STATE_ITERATOR_PLACE_HOLDER
            if state[2][3] < state[2][4] and self._week_balance_invert > 0:
                if self.data[crc][F][HAS_TUT] and do_tut:
                    if do_lec:
                        result_fall = self._state_iterator_fall(self.data[crc][ID], state, 
                                                   (self.data[crc][ID] + (1 << TYPE_SHFT), None), lec_to_ignore, tut_to_ignore)
                    else:
                        result_fall = self._state_iterator_fall(self.data[crc][ID] + (1 << TYPE_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                elif do_lec:
                    result_fall = self._state_iterator_fall(self.data[crc][ID], state, None, lec_to_ignore, tut_to_ignore)            
                if result_fall[0] is None:
                    if self.data[crc][S][HAS_TUT] and do_tut:
                        if do_lec:
                            result_winter = self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, 
                                                       (self.data[crc][ID] + (5 << SESS_SHFT), None), lec_to_ignore, tut_to_ignore)
                        else:
                            result_winter = self._state_iterator_winter(self.data[crc][ID] + (5 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                    elif do_lec:
                        result_winter = self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                    return result_winter
                return result_fall
            elif state[2][3] > state[2][4] and self._week_balance_invert > 0:
                if self.data[crc][S][HAS_TUT] and do_tut:
                    if do_lec:
                        result_winter = self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, 
                                                   (self.data[crc][ID] + (5 << SESS_SHFT), None), lec_to_ignore, tut_to_ignore)
                    else:
                        result_winter = self._state_iterator_winter(self.data[crc][ID] + (5 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                elif do_lec:
                    result_winter = self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                if result_winter[0] is None:
                    if self.data[crc][F][HAS_TUT] and do_tut:
                        if do_lec:
                            result_fall = self._state_iterator_fall(self.data[crc][ID], state, 
                                                       (self.data[crc][ID] + (1 << TYPE_SHFT), None), lec_to_ignore, tut_to_ignore)
                        else:
                            result_fall = self._state_iterator_fall(self.data[crc][ID] + (1 << TYPE_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                    elif do_lec:
                        result_fall = self._state_iterator_fall(self.data[crc][ID], state, None, lec_to_ignore, tut_to_ignore)            
                    return result_fall
                return result_winter
            else:
                if self.data[crc][F][HAS_TUT] and do_tut:
                    if do_lec:
                        result_fall = self._state_iterator_fall(self.data[crc][ID], state, 
                                                   (self.data[crc][ID] + (1 << TYPE_SHFT), None), lec_to_ignore, tut_to_ignore)
                    else:
                        result_fall = self._state_iterator_fall(self.data[crc][ID] + (1 << TYPE_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                elif do_lec:
                    result_fall = self._state_iterator_fall(self.data[crc][ID], state, None, lec_to_ignore, tut_to_ignore)            
                if self.data[crc][S][HAS_TUT] and do_tut:
                    if do_lec:
                        result_winter = self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, 
                                                   (self.data[crc][ID] + (5 << SESS_SHFT), None), lec_to_ignore, tut_to_ignore)
                    else:
                        result_winter = self._state_iterator_winter(self.data[crc][ID] + (5 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                elif do_lec:
                    result_winter = self._state_iterator_winter(self.data[crc][ID] + (1 << SESS_SHFT), state, None, lec_to_ignore, tut_to_ignore)
                if result_fall[0] == None:
                    return result_winter
                elif result_winter[0] == None:
                    return result_fall
                elif result_fall[0][2][2] > result_winter[0][2][2]:
                    return result_fall
                else:
                    return result_winter

    # this function is much more powerful. Can iterate concurrently on any depth. Workers size 18 for depth 4 took ~ 100 seconds.
    def _state_iterator_fall(self, addr: int, state: Tuple[Tuple, Tuple, List], args: Optional[Tuple], lec_to_ignore: List[int], tut_to_ignore: List[int]) -> List:
        comm = [True, False, None, None] # [needed, ready, state_clone, lec_to_ignore_clone]
        def init_cloner(comm: List, state: Tuple[Tuple, Tuple, List], lec_to_ignore: List[int]) -> None:
            while comm[0]:
                if comm[1]:
                    time.sleep(SLEEP)
                    continue
                comm[2] = (((state[0][0][0][:], state[0][0][1][:]),
                            (state[0][1][0][:], state[0][1][1][:]),
                            (state[0][2][0][:], state[0][2][1][:]),
                            (state[0][3][0][:], state[0][3][1][:]),
                            (state[0][4][0][:], state[0][4][1][:]),
                            (state[0][5][0][:], state[0][5][1][:]),
                            (state[0][6][0][:], state[0][6][1][:])),
                           ((state[1][0][0][:], state[1][0][1][:]),
                            (state[1][1][0][:], state[1][1][1][:]),
                            (state[1][2][0][:], state[1][2][1][:]),
                            (state[1][3][0][:], state[1][3][1][:]),
                            (state[1][4][0][:], state[1][4][1][:]),
                            (state[1][5][0][:], state[1][5][1][:]),
                            (state[1][6][0][:], state[1][6][1][:])),
                           [state[2][0][:], state[2][1][:], state[2][2], state[2][3], state[2][4]],
                           (state[3][0][:], state[3][1][:]))
                comm[3] = lec_to_ignore[:]
                comm[1] = True
        threading.Thread(target=init_cloner, args=(comm, state, lec_to_ignore), daemon=True).start()
        workers = []
        crc = self.data[ID][addr & CRC_MASK]
        session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
        type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]
        dict = self.data[crc][session][type]
        to_ignore = lec_to_ignore
        if type == TUTORIALS:
            to_ignore = tut_to_ignore
        i = 0
        for lec in dict[ID]:
            lec_addr = addr + (dict[lec][ID] << LEC_SHFT) + (ASYNC_MAP[dict[lec][ASYNC]] << ASYNC_SHFT)
            if lec_addr in to_ignore:
                continue
            while not comm[1]:
                time.sleep(SLEEP)
            workers.append(Concurrent_Runner(self._try_push_fall, (lec_addr, comm[2], tut_to_ignore, comm[3]), lec_addr))
            comm[1] = False
            workers[i].start()
            i += 1
        comm[0] = False
        best_state = STATE_PLACE_HOLDER
        best_lec_addr = -1
        chk = False
        if args is None:
            while not chk:
                chk = True
                for worker in workers:
                    if worker.is_alive():
                        chk = False
                        continue
                    end_state = worker.join()
                    if end_state is None:
                        continue
                    if end_state[2][2] > best_state[2][2]:
                        best_state = end_state
                        best_lec_addr = worker.ID
                time.sleep(SLEEP)
            if best_lec_addr == -1:
                return [None]
            return [best_state, best_lec_addr]
        best_state = STATE_ITERATOR_PLACE_HOLDER
        while not chk:
            chk = True
            for worker in workers:
                if worker.is_alive():
                    chk = False
                    continue
                end_state = worker.join()
                if end_state is None:
                    continue
                result = self._state_iterator_fall(args[0], end_state, args[1], lec_to_ignore, tut_to_ignore)
                if result[0] is None:
                    continue
                if result[0][2][2] > best_state[0][2][2]:
                    best_state = result
                    best_lec_addr = worker.ID
            time.sleep(SLEEP)
        if best_lec_addr == -1:
                return [None]
        best_state.append(best_lec_addr)
        return best_state

    def _state_iterator_winter(self, addr: int, state: Tuple[Tuple, Tuple, List], args: Optional[Tuple], lec_to_ignore: List[int], tut_to_ignore: List[int]) -> List:
        comm = [True, False, None, None, None] # [needed, ready, state_clone, lec_to_ignore_clone]
        def init_cloner(comm: List, state: Tuple[Tuple, Tuple, List], lec_to_ignore: List[int]) -> None:
            while comm[0]:
                if comm[1]:
                    time.sleep(SLEEP)
                    continue
                comm[2] = (((state[0][0][0][:], state[0][0][1][:]),
                            (state[0][1][0][:], state[0][1][1][:]),
                            (state[0][2][0][:], state[0][2][1][:]),
                            (state[0][3][0][:], state[0][3][1][:]),
                            (state[0][4][0][:], state[0][4][1][:]),
                            (state[0][5][0][:], state[0][5][1][:]),
                            (state[0][6][0][:], state[0][6][1][:])),
                           ((state[1][0][0][:], state[1][0][1][:]),
                            (state[1][1][0][:], state[1][1][1][:]),
                            (state[1][2][0][:], state[1][2][1][:]),
                            (state[1][3][0][:], state[1][3][1][:]),
                            (state[1][4][0][:], state[1][4][1][:]),
                            (state[1][5][0][:], state[1][5][1][:]),
                            (state[1][6][0][:], state[1][6][1][:])),
                           [state[2][0][:], state[2][1][:], state[2][2], state[2][3], state[2][4]],
                           (state[3][0][:], state[3][1][:]))
                comm[3] = lec_to_ignore[:]
                comm[1] = True
        threading.Thread(target=init_cloner, args=(comm, state, lec_to_ignore), daemon=True).start()
        workers = []
        crc = self.data[ID][addr & CRC_MASK]
        session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
        type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]
        dict = self.data[crc][session][type]
        to_ignore = lec_to_ignore
        if type == TUTORIALS:
            to_ignore = tut_to_ignore
        i = 0
        for lec in dict[ID]:
            lec_addr = addr + (dict[lec][ID] << LEC_SHFT) + (ASYNC_MAP[dict[lec][ASYNC]] << ASYNC_SHFT)
            if lec_addr in to_ignore:
                continue
            while not comm[1]:
                time.sleep(SLEEP)
            workers.append(Concurrent_Runner(self._try_push_winter, (lec_addr, comm[2], tut_to_ignore, comm[3]), lec_addr))
            comm[1] = False
            workers[i].start()
            i += 1
        comm[0] = False
        best_state = STATE_PLACE_HOLDER
        best_lec_addr = -1
        chk = False
        if args is None:
            while not chk:
                chk = True
                for worker in workers:
                    if worker.is_alive():
                        chk = False
                        continue
                    end_state = worker.join()
                    if end_state is None:
                        continue
                    if end_state[2][2] > best_state[2][2]:
                        best_state = end_state
                        best_lec_addr = worker.ID
                time.sleep(SLEEP)
            if best_lec_addr == -1:
                return [None]
            return [best_state, best_lec_addr]
        best_state = STATE_ITERATOR_PLACE_HOLDER
        while not chk:
            chk = True
            for worker in workers:
                if worker.is_alive():
                    chk = False
                    continue
                end_state = worker.join()
                if end_state is None:
                    continue
                result = self._state_iterator_winter(args[0], end_state, args[1], lec_to_ignore, tut_to_ignore)
                if result[0] is None:
                    continue
                if result[0][2][2] > best_state[0][2][2]:
                    best_state = result
                    best_lec_addr = worker.ID
            time.sleep(SLEEP)
        if best_lec_addr == -1:
                return [None]
        best_state.append(best_lec_addr)
        return best_state

    # multi-cyclic-stage CDRS (conflict detection-resolution-system), core, parent must handle the concurrency aspects.
    def _try_push_fall(self, addr: int, state: Tuple[Tuple, Tuple, List], tut_attempts: List[int], lec_attempts: List[int]) -> Optional[Tuple[Tuple, Tuple, List]]:
        attempts = tut_attempts[:]
        stg2_attempts = []
        stage = 1
        while TRUE:
            if ASYNC_MAP_R[(addr & ASYNC_MASK) >> ASYNC_SHFT]:
                week_load = state[2][0]
                avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
                week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]     # hierarchical decoding of address
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                state[2][2] += self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE]
                state[3][0].append(addr & CLEAN_MASK)
                return state
            elif stage == 1:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]     # hierarchical decoding of address
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                lec_data = self.data[crc][session][type][lec][SCHEDULE]
                min_priority_tut_conflict = None
                min_priority = MAX_PRIORITY # loose upperbound to number of courses
                # NOTE: maximum total iterations ~ 200:
                for stmp in lec_data:
                    for conflict_addr in state[0][lec_data[stmp][DAY]][1]:
                        if self._overlaps(lec_data[stmp], conflict_addr) and\
                           ((conflict_addr & CLEAN_MASK) not in attempts) and\
                           self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]] < min_priority:
                            min_priority = self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]]
                            min_priority_tut_conflict = conflict_addr
                if min_priority_tut_conflict is None:
                    attempts = tut_attempts[:]
                    stg2_attempts = []
                    stage = 3 # elevation
                    continue
                attempts.append(min_priority_tut_conflict & CLEAN_MASK)
                self._remove_lecture(min_priority_tut_conflict, state)
                result = self._add_course(self.data[ID][conflict_addr & CRC_MASK], state, lec_attempts, attempts, do_lec=False)
                if result[0] is None: # conflicting tutorial removed in process for stage 2
                    stage = 2
                    continue
                # if len(attempts) > 0 and (min_priority_tut_conflict & CRC_MASK) != (attempts[len(attempts) - 1] & CRC_MASK):
                #     stg2_attempts = []
                state = result[0]
                continue
            elif stage == 2:
                # assumptions: stage 1 called already, there is an associated lecture for conflicting course tutorial (removed already).
                lec_addr = None
                if stg2_attempts == []: # do conflicting course discovery on first run
                    crc = attempts[len(attempts) - 1] & CRC_MASK
                    found = False
                    for i in RANGE_SEVEN:
                        for lec in state[0][i][0]:
                            if lec & CRC_MASK == crc:
                                lec_addr = lec
                                found = True
                                break
                        if found:
                            break
                    stg2_attempts.append(lec_addr & CLEAN_MASK)
                else:
                    lec_addr = stg2_attempts[len(stg2_attempts) - 1]
                self._remove_lecture(lec_addr, state)
                result = self._add_course(self.data[ID][lec_addr & CRC_MASK], state, stg2_attempts + lec_attempts, attempts) # not recommeded but necessary
                if result[0] is None:
                    return None
                state = result[0]
                stage = 1
                continue
            else:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]     # hierarchical decoding of address
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                lec_data = self.data[crc][session][type][lec][SCHEDULE]
                min_priority_lec_conflict = None
                min_priority = MAX_PRIORITY # loose upperbound to number of courses
                # NOTE: maximum total iterations ~ 200:
                for stmp in lec_data:
                    for conflict_addr in state[0][lec_data[stmp][DAY]][0]:
                        if self._overlaps(lec_data[stmp], conflict_addr) and\
                           ((conflict_addr & CLEAN_MASK) not in lec_attempts) and\
                           self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]] < min_priority:
                            min_priority = self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]]
                            min_priority_lec_conflict = conflict_addr
                if min_priority_lec_conflict is None:
                    type_ind = (addr & TYPE_MASK) >> TYPE_SHFT
                    week_load = state[2][0]
                    for stmp in lec_data:
                        week_load[lec_data[stmp][DAY]] += lec_data[stmp][LEN]
                        state[0][lec_data[stmp][DAY]][type_ind].append(addr + (lec_data[stmp][DAY] << DAY_SHFT) + (lec_data[stmp][START] << START_SHFT) + (lec_data[stmp][END] << END_SHFT))
                    avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
                    week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
                    state[2][2] += self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE]
                    return state
                lec_attempts.append(min_priority_lec_conflict & CLEAN_MASK)
                self._remove_lecture(min_priority_lec_conflict, state)
                result = None
                if self.data[self.data[ID][min_priority_lec_conflict & CRC_MASK]][SESS_MAP_R[(min_priority_lec_conflict & SESS_MASK) >> SESS_SHFT]][HAS_TUT]:
                    crc = min_priority_lec_conflict & CRC_MASK
                    tut_addr = None
                    found = False
                    for i in RANGE_SEVEN:
                        for lec in state[0][i][1]:
                            if lec & CRC_MASK == crc:
                                tut_addr = lec
                                found = True
                                break
                        if found:
                            break
                    if tut_addr is not None:
                        self._remove_lecture(tut_addr, state)
                        result = self._add_course(self.data[ID][crc], state, lec_attempts, attempts)
                    else:
                        result = self._add_course(self.data[ID][crc], state, lec_attempts, attempts, do_tut=False)
                else:
                    result = self._add_course(self.data[ID][min_priority_lec_conflict & CRC_MASK], state, lec_attempts, attempts, do_tut=False)
                if result[0] is None:
                    return None
                state = result[0]
                stage = 1
                continue

    def _try_push_winter(self, addr: int, state: Tuple[Tuple, Tuple, List], tut_attempts: List[int], lec_attempts: List[int]) -> Optional[Tuple[Tuple, Tuple, List]]:
        attempts = tut_attempts[:]
        stg2_attempts = []
        stage = 1
        while TRUE:
            if ASYNC_MAP_R[(addr & ASYNC_MASK) >> ASYNC_SHFT]:
                week_load = state[2][1]
                avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
                week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]     # hierarchical decoding of address
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                state[2][2] += self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE]
                state[3][1].append(addr & CLEAN_MASK)
                return state
            elif stage == 1:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]     # hierarchical decoding of address
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                lec_data = self.data[crc][session][type][lec][SCHEDULE]
                min_priority_tut_conflict = None
                min_priority = MAX_PRIORITY # loose upperbound to number of courses
                # NOTE: maximum total iterations ~ 200:
                for stmp in lec_data:
                    for conflict_addr in state[1][lec_data[stmp][DAY]][1]:
                        if self._overlaps(lec_data[stmp], conflict_addr) and\
                           ((conflict_addr & CLEAN_MASK) not in attempts) and\
                           self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]] < min_priority:
                            min_priority = self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]]
                            min_priority_tut_conflict = conflict_addr
                if min_priority_tut_conflict is None:
                    attempts = tut_attempts[:]
                    stg2_attempts = []
                    stage = 3 # elevation
                    continue
                attempts.append(min_priority_tut_conflict & CLEAN_MASK)
                self._remove_lecture(min_priority_tut_conflict, state)
                result = self._add_course(self.data[ID][conflict_addr & CRC_MASK], state, lec_attempts, attempts, do_lec=False)
                if result[0] is None: # conflicting tutorial removed in process for stage 2
                    stage = 2
                    continue
                # if len(attempts) > 0 and (min_priority_tut_conflict & CRC_MASK) != (attempts[len(attempts) - 1] & CRC_MASK):
                #     stg2_attempts = []
                state = result[0]
                continue
            elif stage == 2:
                # assumptions: stage 1 called already, there is an associated lecture for conflicting course tutorial (removed already).
                lec_addr = None
                if stg2_attempts == []: # do conflicting course discovery on first run
                    crc = attempts[len(attempts) - 1] & CRC_MASK
                    found = False
                    for i in RANGE_SEVEN:
                        for lec in state[1][i][0]:
                            if lec & CRC_MASK == crc:
                                lec_addr = lec
                                found = True
                                break
                        if found:
                            break
                    stg2_attempts.append(lec_addr & CLEAN_MASK)
                else:
                    lec_addr = stg2_attempts[len(stg2_attempts) - 1]
                self._remove_lecture(lec_addr, state)
                result = self._add_course(self.data[ID][lec_addr & CRC_MASK], state, stg2_attempts + lec_attempts, attempts) # not recommeded, but necessary.
                if result[0] is None:
                    return None
                state = result[0]
                stage = 1
                continue
            else:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]     # hierarchical decoding of address
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                lec_data = self.data[crc][session][type][lec][SCHEDULE]
                min_priority_lec_conflict = None
                min_priority = MAX_PRIORITY # loose upperbound to number of courses
                # NOTE: maximum total iterations ~ 200:
                for stmp in lec_data:
                    for conflict_addr in state[1][lec_data[stmp][DAY]][0]:
                        if self._overlaps(lec_data[stmp], conflict_addr) and\
                           ((conflict_addr & CLEAN_MASK) not in lec_attempts) and\
                           self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]] < min_priority:
                            min_priority = self._priority_map[self.data[ID][conflict_addr & CRC_MASK]][SESS_MAP_R[(conflict_addr & SESS_MASK) >> SESS_SHFT]]
                            min_priority_lec_conflict = conflict_addr
                if min_priority_lec_conflict is None:
                    type_ind = (addr & TYPE_MASK) >> TYPE_SHFT
                    week_load = state[2][1]
                    for stmp in lec_data:
                        week_load[lec_data[stmp][DAY]] += lec_data[stmp][LEN]
                        state[1][lec_data[stmp][DAY]][type_ind].append(addr + (lec_data[stmp][DAY] << DAY_SHFT) + (lec_data[stmp][START] << START_SHFT) + (lec_data[stmp][END] << END_SHFT))
                    avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
                    week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
                    state[2][2] += self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE]
                    return state
                lec_attempts.append(min_priority_lec_conflict & CLEAN_MASK)
                self._remove_lecture(min_priority_lec_conflict, state)
                result = None
                if self.data[self.data[ID][min_priority_lec_conflict & CRC_MASK]][SESS_MAP_R[(min_priority_lec_conflict & SESS_MASK) >> SESS_SHFT]][HAS_TUT]:
                    crc = min_priority_lec_conflict & CRC_MASK
                    tut_addr = None
                    found = False
                    for i in RANGE_SEVEN:
                        for lec in state[1][i][1]:
                            if lec & CRC_MASK == crc:
                                tut_addr = lec
                                found = True
                                break
                        if found:
                            break
                    if tut_addr is not None:
                        self._remove_lecture(tut_addr, state)
                        result = self._add_course(self.data[ID][crc], state, lec_attempts, attempts)
                    else:
                        result = self._add_course(self.data[ID][crc], state, lec_attempts, attempts, do_tut=False)
                else:
                    result = self._add_course(self.data[ID][min_priority_lec_conflict & CRC_MASK], state, lec_attempts, attempts, do_tut=False)
                if result[0] is None:
                    return None
                state = result[0]
                stage = 1
                continue

    # hard lecture removal helper (NO_CHECK_POLICY):
    def _remove_lecture(self, addr: int, state: Tuple[Tuple, Tuple, List]) -> None:
        addr = addr & CLEAN_MASK
        crc = self.data[ID][addr & CRC_MASK]
        session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
        type_ind = (addr & TYPE_MASK) >> TYPE_SHFT
        type = TYPE_MAP_R[type_ind]     # hierarchical decoding of address
        lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
        if ASYNC_MAP_R[(addr & ASYNC_MASK) >> ASYNC_SHFT]:
            if not session == S:
                week_load = state[2][0]
                avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
                week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
                state[2][2] -= (self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE])
                state[3][0].remove(addr)
            if not session == F:
                week_load = state[2][1]
                avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
                week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
                state[2][2] -= (self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE])
                state[3][1].remove(addr)
            return
        lec_data = self.data[crc][session][type][lec][SCHEDULE]
        if not session == S:
            week_load = state[2][0]
            avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
            week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
            state[2][2] -= (self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE])
            for stmp in lec_data:
                week_load[lec_data[stmp][DAY]] -= lec_data[stmp][LEN]
                state[0][lec_data[stmp][DAY]][type_ind].remove(addr + (lec_data[stmp][DAY] << DAY_SHFT) + (lec_data[stmp][START] << START_SHFT) + (lec_data[stmp][END] << END_SHFT))
        if not session == F:
            week_load = state[2][1]
            avg = (week_load[0] + week_load[1] + week_load[2] + week_load[3] + week_load[4] + week_load[5] + week_load[6]) / 7.0
            week_score = abs(avg - week_load[0]) + abs(avg - week_load[1]) + abs(avg - week_load[2]) + abs(avg - week_load[3]) + abs(avg - week_load[4]) + abs(avg - week_load[5]) + abs(avg - week_load[6])
            state[2][2] -= (self._week_weight * self._priority_map[crc][session] * abs(self._week_balance_invert - week_score) + self.data[crc][session][type][lec][TSCORE])
            for stmp in lec_data:
                week_load[lec_data[stmp][DAY]] -= lec_data[stmp][LEN]
                state[1][lec_data[stmp][DAY]][type_ind].remove(addr + (lec_data[stmp][DAY] << DAY_SHFT) + (lec_data[stmp][START] << START_SHFT) + (lec_data[stmp][END] << END_SHFT))

    def print_schedule(self, state: Tuple[Tuple, Tuple, List] = None) -> None:
        if state == None:
            state = self._state
        four = "    "
        eight = "        "
        seperator = "------------------------------------------------------------"
        print(seperator)
        print('fall schedule :')
        for i in RANGE_SEVEN:
            if len(state[0][i][0]) > 0 or len(state[0][i][1]) > 0:
                print(f'{DAYS_LONG[i]} :')
            if len(state[0][i][0]) > 0:
                print(f'{four}lectures :')
            for addr in state[0][i][0]:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                start = (addr & START_MASK) >> START_SHFT
                end = (addr & END_MASK) >> END_SHFT
                start_min = start % 100
                end_min = end % 100
                start_time = None
                end_time = None
                if start_min == 0:
                    start_time = f'{int(start/100)}:00'
                else:
                    start_time = f'{int(start/100)}:{start_min}'
                if end_min == 0:
                    end_time = f'{int(end/100)}:00'
                else:
                    end_time = f'{int(end/100)}:{end_time}'
                print(f'{eight}{crc}{session}-{lec}[{start_time}, {end_time}]')
            if len(state[0][i][1]) > 0:
                print(f'{four}tutorials :')
            for addr in state[0][i][1]:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                start = (addr & START_MASK) >> START_SHFT
                end = (addr & END_MASK) >> END_SHFT
                start_min = start % 100
                end_min = end % 100
                start_time = None
                end_time = None
                if start_min == 0:
                    start_time = f'{int(start/100)}:00'
                else:
                    start_time = f'{int(start/100)}:{start_min}'
                if end_min == 0:
                    end_time = f'{int(end/100)}:00'
                else:
                    end_time = f'{int(end/100)}:{end_time}'
                print(f'{eight}{crc}{session}-{lec}[{start_time}, {end_time}]')
        print(seperator)
        print('winter schedule :')
        for i in RANGE_SEVEN:
            if len(state[1][i][0]) > 0 or len(state[1][i][1]) > 0:
                print(f'{DAYS_LONG[i]} :')
            if len(state[1][i][0]) > 0:
                print(f'{four}lectures :')
            for addr in state[1][i][0]:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                start = (addr & START_MASK) >> START_SHFT
                end = (addr & END_MASK) >> END_SHFT
                start_min = start % 100
                end_min = end % 100
                start_time = None
                end_time = None
                if start_min == 0:
                    start_time = f'{int(start/100)}:00'
                else:
                    start_time = f'{int(start/100)}:{start_min}'
                if end_min == 0:
                    end_time = f'{int(end/100)}:00'
                else:
                    end_time = f'{int(end/100)}:{end_time}'
                print(f'{eight}{crc}{session}-{lec}[{start_time}, {end_time}]')
            if len(state[1][i][1]) > 0:
                print(f'{four}tutorials :')
            for addr in state[1][i][1]:
                crc = self.data[ID][addr & CRC_MASK]
                session = SESS_MAP_R[(addr & SESS_MASK) >> SESS_SHFT]
                type = TYPE_MAP_R[(addr & TYPE_MASK) >> TYPE_SHFT]
                lec = self.data[crc][session][type][ID][(addr & LEC_MASK) >> LEC_SHFT]
                start = (addr & START_MASK) >> START_SHFT
                end = (addr & END_MASK) >> END_SHFT
                start_min = start % 100
                end_min = end % 100
                start_time = None
                end_time = None
                if start_min == 0:
                    start_time = f'{int(start/100)}:00'
                else:
                    start_time = f'{int(start/100)}:{start_min}'
                if end_min == 0:
                    end_time = f'{int(end/100)}:00'
                else:
                    end_time = f'{int(end/100)}:{end_time}'
                print(f'{eight}{crc}{session}-{lec}[{start_time}, {end_time}]')
        print(seperator)
        print('number of fall courses :', state[2][3])
        print('number of winter courses :', state[2][4])
        total = 0.0
        print(f'fall week load :')
        for i in RANGE_SEVEN:
            if state[2][0][i] == 0:
                continue
            print(f'{four}{DAYS_LONG[i]} : {state[2][0][i] / 100} hrs')
            total += state[2][0][i] / 100
        print(f'fall working day average : {round(total / 5, PRECISION)} hrs/day')
        total_ = 0.0
        print(f'winter week load :')
        for i in RANGE_SEVEN:
            if state[2][1][i] == 0:
                continue
            print(f'{four}{DAYS_LONG[i]} : {state[2][1][i] / 100} hrs')
            total_ += state[2][1][i] / 100
        print(f'winter working day average : {round(total_ / 5, PRECISION)} hrs/day')
        print(f'normal load percentage : {round(((total + total_) * 25) / (state[2][3] + state[2][4]), PRECISION)}% of 4 hrs/crc-week')
        print(f'schedule score : {round(state[2][2], PRECISION)}')
        print(seperator)

class Concurrent_Runner(threading.Thread):
    return_value: Optional[Any]
    ID: int

    def __init__(self, func: Callable, args: Tuple, ID: int):
        threading.Thread.__init__(self, target=func, args=args, daemon=True)
        self.return_value = None
        self.ID = ID
    
    def run(self):
        self.return_value = self._target(*self._args, **self._kwargs)

    def join(self):
        threading.Thread.join(self)
        return self.return_value


if __name__ == '__main__':
    #crcs = ['mat137Y', 'csc148S', 'csc165S', 'csc263A', 'phl101Y', 'csc197F', 'mat223F', 'mat224S', 'eco101F']

    # -- editable begin --

    crcs = ['csc148S', 'mat137Y', 'eco101A']
    allow_async = False
    sch = Scheduler(crcs, allow_async, 2021)
    timePrefnsFall = [1200]
    timePrefnsWinter = [1200]
    balanced = True
    weights = [0.3, 0.3] # weekscore ~ 7500 in balanced
    crcPrefns = ['csc148S', 'mat137Y', 'eco101S', 'eco101F'] # descending priority.

    # -- editable end --

    print("Courses read: ", sch.get_read_courses())
    success = sch.make_schedule(timePrefnsFall, timePrefnsWinter, crcPrefns, weights, balanced)
    if(success):
        sch.print_schedule()
