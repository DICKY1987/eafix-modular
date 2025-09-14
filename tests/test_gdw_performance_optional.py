from __future__ import annotations

import pytest


@pytest.mark.skip(reason="performance/chaos tests are optional and environment-dependent")
def test_gdw_performance_placeholder():
    assert True

