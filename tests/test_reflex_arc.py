from brain.regions.cortical_regions import ReflexArc


def test_reflex_blocks_high_force():
    ra = ReflexArc(n=1000)
    cmd = {"force": 20.0, "angle": 10.0, "velocity": 0.1}
    res = ra.check_command(cmd)
    assert res["approved"] is False
    assert "REFLEX_WITHDRAWAL" in res["reason"]
