"""
persistence/brain_store.py — Brain State Persistence
====================================================
Saves and loads complete brain state to/from disk.
"""

import os
import json
import numpy as np
from typing import Optional, List, Any
from dataclasses import asdict


class BrainStore:
    """
    Saves and loads complete brain state to/from disk.
    
    Directory structure:
      brain_state/
        self_model.json          ← identity, personality, stats
        synapses/
          sensory_feature.npz    ← sparse weight arrays (COO format)
          feature_assoc.npz
          assoc_predictive.npz
          ... (one file per synapse group)
        vocabulary/
          lexical_stdp.npz       ← word ↔ assembly weights (sparse)
          assembly_labels.json   ← assembly_id → top words
        memory/
          hippocampus_weights.npz← CA3 recurrent weights
          episode_index.json     ← episode metadata (timestamps, topics)
        drives/
          drive_history.json     ← 1000-turn rolling history
        affect/
          affect_history.json    ← valence/arousal over time
    
    Save frequency:
      Full save:    every 10,000 steps or on graceful shutdown
      Self-model:   every turn (lightweight, critical)
      Synapses:     every 10,000 steps (expensive, less critical)
    """
    
    BASE_DIR = "brain_state"
    
    def __init__(self, base_dir: Optional[str] = None):
        self.BASE_DIR = base_dir or os.getenv("BRAIN_STATE_DIR", "brain_state")
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories."""
        os.makedirs(self.BASE_DIR, exist_ok=True)
        os.makedirs(f"{self.BASE_DIR}/synapses", exist_ok=True)
        os.makedirs(f"{self.BASE_DIR}/vocabulary", exist_ok=True)
        os.makedirs(f"{self.BASE_DIR}/memory", exist_ok=True)
        os.makedirs(f"{self.BASE_DIR}/drives", exist_ok=True)
        os.makedirs(f"{self.BASE_DIR}/affect", exist_ok=True)
    
    # ─── Self Model ───────────────────────────────────────────────────────────
    
    def save_self_model(self, model: Any) -> bool:
        """
        Save self model to disk.
        
        Parameters
        ----------
        model : SelfModel
            The self model to save
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            model.save(f"{self.BASE_DIR}/self_model.json")
            return True
        except Exception as e:
            print(f"Error saving self model: {e}")
            return False
    
    def load_self_model(self) -> Optional[Any]:
        """
        Load self model from disk.
        
        Returns
        -------
        Optional[SelfModel]
            The loaded self model, or None if not found
        """
        from self.self_model import SelfModel
        path = f"{self.BASE_DIR}/self_model.json"
        if os.path.exists(path):
            try:
                return SelfModel.load(path)
            except Exception as e:
                print(f"Error loading self model: {e}")
        return None
    
    # ─── Synapses ─────────────────────────────────────────────────────────────
    
    def save_synapses(self, synapses: List[Any]) -> int:
        """
        Save all synapse groups to disk.
        
        Parameters
        ----------
        synapses : list
            List of SparseSTDPSynapse objects
            
        Returns
        -------
        int
            Number of synapse groups saved
        """
        try:
            import scipy.sparse
        except ImportError:
            print("[BrainStore] scipy not available - synapse save disabled")
            return 0
        
        saved = 0
        for syn in synapses:
            try:
                safe_name = syn.name.replace("→", "_to_").replace(" ", "_")
                path = f"{self.BASE_DIR}/synapses/{safe_name}.npz"
                
                # Convert to sparse matrix and save
                mat = scipy.sparse.coo_matrix(
                    (syn.weights, (syn.pre_idx, syn.post_idx)),
                    shape=(syn.pre_n, syn.post_n)
                )
                scipy.sparse.save_npz(path, mat)
                saved += 1
            except Exception as e:
                print(f"Error saving synapse {syn.name}: {e}")
        
        return saved
    
    def load_synapses(self, synapse: Any) -> bool:
        """
        Load a single synapse group from disk.
        
        Parameters
        ----------
        synapse : SparseSTDPSynapse
            The synapse to load into
            
        Returns
        -------
        bool
            True if loaded successfully
        """
        try:
            import scipy.sparse
        except ImportError:
            print("[BrainStore] scipy not available - synapse load disabled")
            return False
        
        try:
            safe_name = synapse.name.replace("→", "_to_").replace(" ", "_")
            path = f"{self.BASE_DIR}/synapses/{safe_name}.npz"
            
            if os.path.exists(path):
                mat = scipy.sparse.load_npz(path).tocoo()
                # Filter out any synapses that reference neurons outside the
                # current brain scale (pre/post sizes may differ between runs).
                rows = mat.row.astype(np.int32)
                cols = mat.col.astype(np.int32)
                data = mat.data.astype(np.float32)

                valid_mask = (rows >= 0) & (rows < synapse.pre_n) & (cols >= 0) & (cols < synapse.post_n)
                if not valid_mask.all():
                    # Some saved synapses are out-of-range for this instantiation — drop them
                    rows = rows[valid_mask]
                    cols = cols[valid_mask]
                    data = data[valid_mask]
                    print(f"[BrainStore] Warning: clipped {valid_mask.size - valid_mask.sum()} synapses when loading {synapse.name}")

                synapse.weights = data
                synapse.pre_idx = rows
                synapse.post_idx = cols
                return True
        except Exception as e:
            print(f"Error loading synapse {synapse.name}: {e}")
        
        return False
    
    def save_all_synapses(self, synapses: List[Any]) -> int:
        """
        Save all synapses and return count.
        Alias for save_synapses.
        """
        return self.save_synapses(synapses)
    
    def load_all_synapses(self, synapses: List[Any]) -> int:
        """
        Load all synapses and return count of loaded.
        """
        loaded = 0
        for syn in synapses:
            if self.load_synapses(syn):
                loaded += 1
        return loaded
    
    # ─── Vocabulary ───────────────────────────────────────────────────────────

    def save_vocabulary_export(self, vocab_data: dict) -> bool:
        """Save full phonological buffer vocabulary export to disk.

        Expected format is compatible with PhonologicalBuffer.export_vocabulary():
        {
          "word_index": {word: id, ...},
          "id_to_word": {id: word, ...},
          "a2w": {assembly_id: {word_id: weight}},
          "w2a": {word_id: {assembly_id: weight}},
          "word_order": [...]
        }
        """
        try:
            vocab_dir = f"{self.BASE_DIR}/vocabulary"
            os.makedirs(vocab_dir, exist_ok=True)

            with open(f"{vocab_dir}/word_to_assembly.json", "w", encoding="utf-8") as f:
                json.dump(vocab_data.get("w2a", {}), f)
            with open(f"{vocab_dir}/assembly_to_words.json", "w", encoding="utf-8") as f:
                json.dump(vocab_data.get("a2w", {}), f)
            with open(f"{vocab_dir}/word_index.json", "w", encoding="utf-8") as f:
                json.dump(vocab_data.get("word_index", {}), f)
            with open(f"{vocab_dir}/id_to_word.json", "w", encoding="utf-8") as f:
                json.dump(vocab_data.get("id_to_word", {}), f)
            with open(f"{vocab_dir}/word_order.json", "w", encoding="utf-8") as f:
                json.dump(vocab_data.get("word_order", []), f)

            return True
        except Exception as e:
            print(f"Error saving vocabulary export: {e}")
            return False

    def load_vocabulary_export(self) -> dict:
        """Load full phonological buffer vocabulary export from disk."""
        vocab_dir = f"{self.BASE_DIR}/vocabulary"
        data: dict = {
            "w2a": {},
            "a2w": {},
            "word_index": {},
            "id_to_word": {},
            "word_order": [],
        }
        try:
            w2a_path = f"{vocab_dir}/word_to_assembly.json"
            a2w_path = f"{vocab_dir}/assembly_to_words.json"
            idx_path = f"{vocab_dir}/word_index.json"
            idw_path = f"{vocab_dir}/id_to_word.json"
            worder_path = f"{vocab_dir}/word_order.json"

            if os.path.exists(w2a_path):
                with open(w2a_path, "r", encoding="utf-8") as f:
                    data["w2a"] = json.load(f)
            if os.path.exists(a2w_path):
                with open(a2w_path, "r", encoding="utf-8") as f:
                    data["a2w"] = json.load(f)
            if os.path.exists(idx_path):
                with open(idx_path, "r", encoding="utf-8") as f:
                    data["word_index"] = json.load(f)
            if os.path.exists(idw_path):
                with open(idw_path, "r", encoding="utf-8") as f:
                    data["id_to_word"] = json.load(f)
            if os.path.exists(worder_path):
                with open(worder_path, "r", encoding="utf-8") as f:
                    data["word_order"] = json.load(f)
        except Exception as e:
            print(f"Error loading vocabulary export: {e}")
        return data
    
    def save_vocabulary(self, word_to_assembly: dict, assembly_to_words: dict) -> bool:
        """
        Save vocabulary (word ↔ assembly mappings).
        
        Parameters
        ----------
        word_to_assembly : dict
            Mapping from word to assembly
        assembly_to_words : dict
            Mapping from assembly to list of words
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            # Save word to assembly
            with open(f"{self.BASE_DIR}/vocabulary/word_to_assembly.json", "w") as f:
                json.dump(word_to_assembly, f)
            
            # Save assembly to words
            with open(f"{self.BASE_DIR}/vocabulary/assembly_to_words.json", "w") as f:
                json.dump(assembly_to_words, f)
            
            return True
        except Exception as e:
            print(f"Error saving vocabulary: {e}")
            return False
    
    def load_vocabulary(self) -> tuple:
        """
        Load vocabulary.
        
        Returns
        -------
        tuple
            (word_to_assembly, assembly_to_words)
        """
        w2a = {}
        a2w = {}
        
        try:
            path = f"{self.BASE_DIR}/vocabulary/word_to_assembly.json"
            if os.path.exists(path):
                with open(path) as f:
                    w2a = json.load(f)
            
            path = f"{self.BASE_DIR}/vocabulary/assembly_to_words.json"
            if os.path.exists(path):
                with open(path) as f:
                    a2w = json.load(f)
        except Exception as e:
            print(f"Error loading vocabulary: {e}")
        
        return w2a, a2w
    
    # ─── Drive History ───────────────────────────────────────────────────────
    
    def save_drive_history(self, history: List[dict]) -> bool:
        """
        Save drive history.
        
        Parameters
        ----------
        history : list
            List of drive states
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            # Keep only last 1000 entries
            history = history[-1000:]
            with open(f"{self.BASE_DIR}/drives/drive_history.json", "w") as f:
                json.dump(history, f)
            return True
        except Exception as e:
            print(f"Error saving drive history: {e}")
            return False
    
    def load_drive_history(self) -> List[dict]:
        """
        Load drive history.
        
        Returns
        -------
        list
            Drive history
        """
        try:
            path = f"{self.BASE_DIR}/drives/drive_history.json"
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading drive history: {e}")
        return []
    
    # ─── Affect History ───────────────────────────────────────────────────────
    
    def save_affect_history(self, history: List[dict]) -> bool:
        """
        Save affect history.
        
        Parameters
        ----------
        history : list
            List of affect states
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            # Keep only last 1000 entries
            history = history[-1000:]
            with open(f"{self.BASE_DIR}/affect/affect_history.json", "w") as f:
                json.dump(history, f)
            return True
        except Exception as e:
            print(f"Error saving affect history: {e}")
            return False
    
    def load_affect_history(self) -> List[dict]:
        """
        Load affect history.
        
        Returns
        -------
        list
            Affect history
        """
        try:
            path = f"{self.BASE_DIR}/affect/affect_history.json"
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading affect history: {e}")
        return []
    
    # ─── Full State ───────────────────────────────────────────────────────────
    
    def save_full(self, brain) -> bool:
        """
        Save complete brain state.
        
        Parameters
        ----------
        brain : BRAIN2.0Brain
            The brain to save
            
        Returns
        -------
        bool
            True if successful
        """
        try:
            # Save self model
            self.save_self_model(brain.self_model)
            
            # Save synapses (less frequent, but do it here)
            self.save_synapses(brain.all_synapses)
            
            # Save vocabulary if available
            if hasattr(brain, 'phon_buffer'):
                self.save_vocabulary_export(brain.phon_buffer.export_vocabulary())
            
            return True
        except Exception as e:
            print(f"Error saving full brain state: {e}")
            return False
    
    def load_full(self, brain) -> bool:
        """
        Load complete brain state.
        
        Parameters
        ----------
        brain : BRAIN2.0Brain
            The brain to load into
            
        Returns
        -------
        bool
            True if loaded successfully
        """
        try:
            # Load self model
            model = self.load_self_model()
            if model:
                brain.self_model = model
            
            # Load synapses
            loaded = self.load_all_synapses(brain.all_synapses)
            print(f"Loaded {loaded}/{len(brain.all_synapses)} synapse groups")
            
            # Load vocabulary if brain has phon_buffer
            if hasattr(brain, 'phon_buffer'):
                vocab_data = self.load_vocabulary_export()
                if vocab_data.get('w2a') or vocab_data.get('word_index'):
                    brain.phon_buffer.import_vocabulary(vocab_data)
            
            return True
        except Exception as e:
            print(f"Error loading full brain state: {e}")
            return False
    
    # ─── Utility ─────────────────────────────────────────────────────────────
    
    def exists(self) -> bool:
        """Check if any brain state exists on disk."""
        return os.path.exists(f"{self.BASE_DIR}/self_model.json")
    
    def get_state_size(self) -> int:
        """
        Get approximate size of saved state in bytes.
        
        Returns
        -------
        int
            Size in bytes
        """
        total = 0
        for root, dirs, files in os.walk(self.BASE_DIR):
            for f in files:
                path = os.path.join(root, f)
                total += os.path.getsize(path)
        return total
    
    def clear(self) -> bool:
        """
        Clear all saved brain state.
        
        Returns
        -------
        bool
            True if successful
        """
        try:
            import shutil
            if os.path.exists(self.BASE_DIR):
                shutil.rmtree(self.BASE_DIR)
            self._ensure_directories()
            return True
        except Exception as e:
            print(f"Error clearing brain state: {e}")
            return False


def create_brain_store(base_dir: str = "brain_state") -> BrainStore:
    """Create a default brain store."""
    return BrainStore(base_dir)


if __name__ == "__main__":
    # Test the BrainStore
    store = create_brain_store("test_brain_state")
    
    # Check if state exists
    print(f"State exists: {store.exists()}")
    print(f"State size: {store.get_state_size()} bytes")
    
    # Clean up test directory
    if os.path.exists("test_brain_state"):
        import shutil
        shutil.rmtree("test_brain_state")
