import os
from unittest import TestCase

from .bwh import BWH


class Test(TestCase):
    def test_query_bwh(self):
        bwh = BWH(os.environ['veid'], os.environ['api_key'])
        assert bwh.used_bandwidth is not None
        print(bwh.used_bandwidth)

