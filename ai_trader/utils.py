from typing import List


def check_rules(conds: List[bool], cutoff: int):
    cnt = 0
    for cond in conds:
        if not cond:
            cnt += 1
        if cnt >= cutoff:
            return True
    return False
