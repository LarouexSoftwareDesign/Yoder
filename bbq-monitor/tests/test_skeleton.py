# -*- coding: utf-8 -*-

import pytest
from bbq_monitor.skeleton import fib

__author__ = "Larry W Jordan Jr"
__copyright__ = "Larry W Jordan Jr"
__license__ = "mit"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
