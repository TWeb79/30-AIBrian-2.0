"""
cognition/cell_assemblies.py — Cell Assembly Detector
======================================================
Tracks which concept neurons fire together repeatedly.
When a stable coalition fires on consecutive observations,
registers it as a named assembly with a unique ID.

This replaces the single-concept-id tracking in ConceptLayer
with multi-neuron coalition detection.
"""

import numpy as np
from typing import Optional, Dict, List, Set, Any


class CellAssemblyDetector:
    """
    Detects and tracks stable neuron assemblies via co-firing.
    
    An assembly is a group of concept neurons that fire together
    repeatedly across consecutive turns. Once a coalition appears
    `stability_threshold` times, it's registered as a named assembly.
    
    This is the bridge between raw spike patterns and the
    PhonologicalBuffer's word↔assembly maps.
    """
    
    def __init__(
        self,
        n_concept_neurons: int,
        min_coalition_size: int = 2,
        stability_threshold: int = 2,
        overlap_threshold: float = 0.5,
    ):
        self.n = n_concept_neurons
        self.min_coalition_size = min_coalition_size
        self.stability_threshold = stability_threshold
        self.overlap_threshold = overlap_threshold
        
        # Registered assemblies: {assembly_id: frozenset(neuron_ids)}
        self.assemblies: Dict[int, frozenset] = {}
        self._next_id = 0
        
        # Tracking for stability detection
        self._coalition_counts: Dict[frozenset, int] = {}
        self._last_coalition: Optional[frozenset] = None
        
        # Activity tracking
        self._assembly_activation_counts: Dict[int, int] = {}
    
    def get_or_create_assembly(self, active_neuron_ids: Set[int]) -> int:
        """
        Given currently active concept neurons, find or create an assembly.
        
        Parameters
        ----------
        active_neuron_ids : set[int]
            IDs of concept neurons that fired this turn
            
        Returns
        -------
        int
            Assembly ID (0-indexed), or -1 if too few neurons
        """
        if len(active_neuron_ids) < self.min_coalition_size:
            return -1
        
        coalition = frozenset(active_neuron_ids)
        
        # Check if this coalition matches an existing assembly
        best_id = -1
        best_overlap = 0.0
        
        for asm_id, asm_neurons in self.assemblies.items():
            if not asm_neurons:
                continue
            overlap = len(coalition & asm_neurons) / len(asm_neurons)
            if overlap > self.overlap_threshold and overlap > best_overlap:
                best_overlap = overlap
                best_id = asm_id
        
        if best_id >= 0:
            # Existing assembly — track activation
            self._assembly_activation_counts[best_id] = \
                self._assembly_activation_counts.get(best_id, 0) + 1
            # Slowly expand assembly with new co-firing neurons
            old = self.assemblies[best_id]
            self.assemblies[best_id] = frozenset(old | coalition)
            return best_id
        
        # New coalition — check stability
        self._coalition_counts[coalition] = \
            self._coalition_counts.get(coalition, 0) + 1
        
        if self._coalition_counts[coalition] >= self.stability_threshold:
            # Stable coalition → register as assembly
            new_id = self._next_id
            self._next_id += 1
            self.assemblies[new_id] = coalition
            self._assembly_activation_counts[new_id] = \
                self._coalition_counts[coalition]
            return new_id
        
        # Not yet stable — return -1 (still observing)
        return -1
    
    def get_active_assemblies(self, active_neuron_ids: Set[int]) -> List[int]:
        """
        Find all assemblies that overlap with current activity.
        
        Returns
        -------
        list[int]
            Assembly IDs with overlap > threshold, sorted by overlap desc
        """
        if not active_neuron_ids:
            return []
        
        results = []
        for asm_id, asm_neurons in self.assemblies.items():
            if not asm_neurons:
                continue
            overlap = len(active_neuron_ids & asm_neurons) / len(asm_neurons)
            if overlap > self.overlap_threshold:
                results.append((asm_id, overlap))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]
    
    def get_assembly_neurons(self, assembly_id: int) -> Set[int]:
        """Return neuron IDs for an assembly."""
        return set(self.assemblies.get(assembly_id, frozenset()))
    
    def get_top_assemblies(self, top_k: int = 5) -> List[tuple]:
        """
        Return most active assemblies.
        
        Returns
        -------
        list[tuple]
            [(assembly_id, activation_count, neuron_count), ...]
        """
        ranked = sorted(
            self._assembly_activation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        return [
            (aid, count, len(self.assemblies.get(aid, frozenset())))
            for aid, count in ranked
        ]
    
    def get_assembly_count(self) -> int:
        """Number of stable registered assemblies."""
        return len(self.assemblies)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_assemblies": len(self.assemblies),
            "pending_coalitions": len(self._coalition_counts) - len(self.assemblies),
            "top_assemblies": self.get_top_assemblies(5),
            "total_activations": sum(self._assembly_activation_counts.values()),
        }
    
    def export(self) -> Dict[str, Any]:
        """Export for persistence."""
        return {
            "assemblies": {str(k): list(v) for k, v in self.assemblies.items()},
            "next_id": self._next_id,
            "activation_counts": {str(k): v for k, v in self._assembly_activation_counts.items()},
        }
    
    def import_(self, data: Dict[str, Any]):
        """Import from persistence."""
        if "assemblies" in data:
            self.assemblies = {int(k): frozenset(v) for k, v in data["assemblies"].items()}
        if "next_id" in data:
            self._next_id = data["next_id"]
        if "activation_counts" in data:
            self._assembly_activation_counts = {int(k): v for k, v in data["activation_counts"].items()}


def create_cell_assembly_detector(n_concept_neurons: int) -> CellAssemblyDetector:
    return CellAssemblyDetector(n_concept_neurons)
