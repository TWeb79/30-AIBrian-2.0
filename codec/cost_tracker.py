"""
codec/cost_tracker.py — API Cost Tracking
==========================================
Tracks LLM API usage and enforces budget limits.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class CallRecord:
    """Record of a single LLM call."""
    timestamp: float
    tokens_in: int
    tokens_out: int
    cost: float
    model: str


class CostTracker:
    """
    Tracks LLM API usage and enforces budget limits.
    
    Usage:
      - Tracks daily, monthly, and all-time spend
      - Enforces budget limits with configurable actions
      - Provides statistics for monitoring
    """
    
    # Default budget limits (in USD)
    DEFAULT_DAILY_BUDGET = 0.50
    DEFAULT_MONTHLY_BUDGET = 10.00
    
    # Default pricing (per 1M tokens) - GPT-4o-mini
    DEFAULT_INPUT_PRICE = 0.15
    DEFAULT_OUTPUT_PRICE = 0.60
    
    def __init__(
        self,
        daily_budget: float = DEFAULT_DAILY_BUDGET,
        monthly_budget: float = DEFAULT_MONTHLY_BUDGET,
        input_price: float = DEFAULT_INPUT_PRICE,
        output_price: float = DEFAULT_OUTPUT_PRICE,
    ):
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.input_price = input_price
        self.output_price = output_price
        
        # Usage tracking
        self.daily_spend: List[tuple[float, float]] = []  # (timestamp, amount)
        self.monthly_spend: List[tuple[float, float]] = []
        self.total_spend = 0.0
        
        self.call_history: List[CallRecord] = []
        self.max_history = 1000
        
        # Statistics
        self.total_calls = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.last_call_cost = 0.0
        self.last_call_time = 0.0
        
        # Budget enforcement
        self.budget_exceeded = False
        self.action_on_budget_exceeded = "force_local"  # force_local or disable
    
    def track_call(
        self,
        tokens_in: int,
        tokens_out: int,
        model: str = "gpt-4o-mini",
    ) -> float:
        """
        Track a single LLM call.
        
        Parameters
        ----------
        tokens_in : int
            Number of input tokens
        tokens_out : int
            Number of output tokens
        model : str
            Model used
            
        Returns
        -------
        float
            Cost of this call
        """
        cost = self._calculate_cost(tokens_in, tokens_out)
        
        now = time.time()
        
        # Record call
        record = CallRecord(
            timestamp=now,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            model=model,
        )
        self.call_history.append(record)
        self.total_calls += 1
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        self.last_call_cost = cost
        self.last_call_time = now
        
        # Update spend tracking
        self.daily_spend.append((now, cost))
        self.monthly_spend.append((now, cost))
        self.total_spend += cost
        
        # Clean old entries (keep last 24 hours for daily, 30 days for monthly)
        self._clean_old_entries()
        
        # Check budgets
        self._check_budgets()
        
        # Trim history
        if len(self.call_history) > self.max_history:
            self.call_history = self.call_history[-self.max_history:]
        
        return cost
    
    def _calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for tokens."""
        in_cost = tokens_in * self.input_price / 1_000_000
        out_cost = tokens_out * self.output_price / 1_000_000
        return in_cost + out_cost
    
    def _clean_old_entries(self):
        """Remove old spend entries."""
        now = time.time()
        
        # Keep last 24 hours for daily (86400 seconds)
        self.daily_spend = [
            (ts, amt) for ts, amt in self.daily_spend
            if now - ts < 86400
        ]
        
        # Keep last 30 days for monthly (30 * 86400 seconds)
        self.monthly_spend = [
            (ts, amt) for ts, amt in self.monthly_spend
            if now - ts < 30 * 86400
        ]
    
    def _check_budgets(self):
        """Check if budgets are exceeded."""
        current_daily = sum(amt for _, amt in self.daily_spend)
        current_monthly = sum(amt for _, amt in self.monthly_spend)
        
        if current_daily >= self.daily_budget:
            self.budget_exceeded = True
        elif current_monthly >= self.monthly_budget:
            self.budget_exceeded = True
        else:
            self.budget_exceeded = False
    
    def can_call_llm(self) -> bool:
        """Check if LLM can be called within budget."""
        if self.action_on_budget_exceeded == "force_local":
            return not self.budget_exceeded
        return True
    
    def get_current_daily_spend(self) -> float:
        """Get current daily spend."""
        return sum(amt for _, amt in self.daily_spend)
    
    def get_current_monthly_spend(self) -> float:
        """Get current monthly spend."""
        return sum(amt for _, amt in self.monthly_spend)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cost statistics."""
        daily = self.get_current_daily_spend()
        monthly = self.get_current_monthly_spend()
        
        avg_cost = self.total_spend / self.total_calls if self.total_calls > 0 else 0
        
        return {
            "total_calls": self.total_calls,
            "total_spend": self.total_spend,
            "daily_spend": daily,
            "daily_budget": self.daily_budget,
            "daily_remaining": self.daily_budget - daily,
            "monthly_spend": monthly,
            "monthly_budget": self.monthly_budget,
            "monthly_remaining": self.monthly_budget - monthly,
            "average_call_cost": avg_cost,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "budget_exceeded": self.budget_exceeded,
        }
    
    def get_recent_calls(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recent calls."""
        recent = self.call_history[-n:]
        return [
            {
                "timestamp": call.timestamp,
                "datetime": datetime.fromtimestamp(call.timestamp).isoformat(),
                "tokens_in": call.tokens_in,
                "tokens_out": call.tokens_out,
                "cost": call.cost,
                "model": call.model,
            }
            for call in recent
        ]
    
    def reset(self):
        """Reset all tracking."""
        self.daily_spend = []
        self.monthly_spend = []
        self.total_spend = 0.0
        self.call_history = []
        self.total_calls = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.budget_exceeded = False
    
    def set_budget(self, budget_type: str, amount: float):
        """
        Set budget limits.
        
        Parameters
        ----------
        budget_type : str
            "daily" or "monthly"
        amount : float
            Budget amount in USD
        """
        if budget_type == "daily":
            self.daily_budget = amount
        elif budget_type == "monthly":
            self.monthly_budget = amount
        self._check_budgets()


def create_cost_tracker() -> CostTracker:
    """Create a default cost tracker."""
    return CostTracker()


if __name__ == "__main__":
    # Test the CostTracker
    tracker = create_cost_tracker()
    
    # Simulate some calls
    for i in range(5):
        tokens_in = 100 + i * 10
        tokens_out = 50 + i * 5
        cost = tracker.track_call(tokens_in, tokens_out)
        print(f"Call {i+1}: {tokens_in} in, {tokens_out} out, cost ${cost:.4f}")
    
    print(f"\nStats: {tracker.get_statistics()}")
    print(f"\nRecent calls: {tracker.get_recent_calls()}")
