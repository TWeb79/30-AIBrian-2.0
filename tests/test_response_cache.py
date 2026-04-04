from codec.response_cache import ResponseCache


def test_response_cache_hit():
    rc = ResponseCache(max_size=10, similarity_threshold=0.5)
    rc.store("hello world", "greeting")
    got = rc.lookup("hello world")
    assert got == "greeting", "Exact match should return stored response"


def test_response_cache_miss():
    """Test that unknown inputs return None."""
    rc = ResponseCache(max_size=10)
    result = rc.lookup("completely new input string here")
    assert result is None, "Unknown input should return None"


def test_response_cache_size_limit():
    """Test that cache respects max_size."""
    rc = ResponseCache(max_size=3)
    rc.store("a", "1")
    rc.store("b", "2")
    rc.store("c", "3")
    rc.store("d", "4")
    
    assert rc.get_size() <= 3, "Cache size should not exceed max_size"


def test_response_cache_stats():
    """Test cache statistics."""
    rc = ResponseCache(max_size=10)
    rc.store("hello", "hi")
    rc.lookup("hello")
    rc.lookup("unknown")
    
    stats = rc.get_statistics()
    assert "size" in stats
    assert "hits" in stats
    assert "misses" in stats
    assert stats["hits"] >= 1, "Should have at least one hit"


def test_response_cache_similarity():
    """Test that similar inputs are detected."""
    rc = ResponseCache(max_size=10, similarity_threshold=0.3)
    rc.store("hello world", "response one")
    
    result = rc.lookup("hello world test")
    assert result is not None, "Similar input should return cached response"


def test_response_cache_export_import():
    """Test cache export/import."""
    rc = ResponseCache(max_size=10)
    rc.store("test input", "test response")
    
    exported = rc.export()
    assert len(exported) > 0, "Export should return entries"
    
    rc2 = ResponseCache(max_size=10)
    rc2.import_(exported)
    result = rc2.lookup("test input")
    assert result == "test response", "Imported cache should work"


if __name__ == "__main__":
    test_response_cache_hit()
    test_response_cache_miss()
    test_response_cache_size_limit()
    test_response_cache_stats()
    test_response_cache_similarity()
    test_response_cache_export_import()
    print("✓ All ResponseCache tests passed!")
