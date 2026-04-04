import os
import shutil
import tempfile

from persistence.brain_store import BrainStore
from codec.phonological_buffer import PhonologicalBuffer


def test_vocabulary_export_roundtrip():
    tmp = tempfile.mkdtemp(prefix="brain_state_")
    try:
        store = BrainStore(base_dir=tmp)

        pb = PhonologicalBuffer(n_assemblies=50)
        # learn a small vocab
        pb.observe_pairing("hello", 1)
        pb.observe_pairing("world", 1)
        export = pb.export_vocabulary()

        assert store.save_vocabulary_export(export) is True
        loaded = store.load_vocabulary_export()

        pb2 = PhonologicalBuffer(n_assemblies=50)
        pb2.import_vocabulary(loaded)
        assert pb2.get_vocabulary_size() >= 2
        assert "hello" in pb2.word_index
        assert "world" in pb2.word_index
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
