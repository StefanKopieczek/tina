from datetime import datetime
import unittest
from datetime import date
from .persistence import _get_epoch_day_for_date


class TestEpochCalculations(unittest.TestCase):
    def test_epoch_zero(self):
        self.assertEqual(_get_epoch_day_for_date(date(1970, 1, 1)), 0)

    def test_3rd_july_2022(self):
        self.assertEqual(_get_epoch_day_for_date(date(2022, 7, 3)), 19176)
