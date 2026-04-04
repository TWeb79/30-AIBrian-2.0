from codec.response_cache import ResponseCache


def test_response_cache_hit():
    rc = ResponseCache(max_size=10, similarity_threshold=0.5)
    rc.store("hello world", "greeting")
    got = rc.lookup("hello world")
    assert got == "greeting"
