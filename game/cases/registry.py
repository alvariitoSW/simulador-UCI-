"""Registro central de los casos clínicos jugables."""
from game.cases.case1_sepsis import SepsisCase
from game.cases.case2_ards import ArdsCase
from game.cases.case3_arrest import ArrestCase
from game.cases.case4_sedation import SedationCase

CASES = [SepsisCase, ArdsCase, ArrestCase, SedationCase]

CASES_BY_ID = {c.case_id: c for c in CASES}
