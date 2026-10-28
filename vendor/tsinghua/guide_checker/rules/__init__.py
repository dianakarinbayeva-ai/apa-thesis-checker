from .m1_structure import RULE_CHECKERS as M1_RULE_CHECKERS
from .m2_cover_abstract import RULE_CHECKERS as M2_RULE_CHECKERS
from .m3_toc_body_page import RULE_CHECKERS as M3_RULE_CHECKERS
from .m4_fig_table import RULE_CHECKERS as M4_RULE_CHECKERS
from .m5_bibliography import RULE_CHECKERS as M5_RULE_CHECKERS
from .m6_abbr_unit_equation import RULE_CHECKERS as M6_RULE_CHECKERS
from .m7_front_back_misc import RULE_CHECKERS as M7_RULE_CHECKERS
from .m8_list_foot_tab import RULE_CHECKERS as M8_RULE_CHECKERS

RULE_CHECKERS = {}
for mapping in (
    M1_RULE_CHECKERS,
    M2_RULE_CHECKERS,
    M3_RULE_CHECKERS,
    M4_RULE_CHECKERS,
    M5_RULE_CHECKERS,
    M6_RULE_CHECKERS,
    M7_RULE_CHECKERS,
    M8_RULE_CHECKERS,
):
    RULE_CHECKERS.update(mapping)

__all__ = ["RULE_CHECKERS"]
