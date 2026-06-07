"""Penalty calculation strategies using the Strategy Pattern (GoF).

Provides different algorithms for calculating overdue invoice penalties:
- FlatRatePenalty: Fixed daily amount
- PercentagePenalty: Percentage of base amount per day
- ProgressivePenalty: Escalating tiers based on days overdue
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.invoice import Invoice


class PenaltyStrategy(ABC):
    """Abstract base class for penalty calculation strategies.

    Implements the Strategy pattern to allow interchangeable
    penalty calculation algorithms.
    """

    @abstractmethod
    def calculate(self, invoice: Invoice, days_overdue: int) -> float:
        """Calculate the penalty amount for an overdue invoice.

        Args:
            invoice: The overdue invoice.
            days_overdue: Number of days past the due date.

        Returns:
            Calculated penalty amount.
        """


class FlatRatePenalty(PenaltyStrategy):
    """Flat rate penalty: fixed amount per day overdue.

    Attributes:
        daily_rate: Fixed penalty amount charged per day.
    """

    def __init__(self, daily_rate: float = 10.0) -> None:
        """Initialize with a daily penalty rate.

        Args:
            daily_rate: Fixed amount per overdue day. Defaults to 10.0.
        """
        self._daily_rate = daily_rate

    @property
    def daily_rate(self) -> float:
        """Get the daily penalty rate."""
        return self._daily_rate

    def calculate(self, invoice: Invoice, days_overdue: int) -> float:
        """Calculate flat-rate penalty.

        Args:
            invoice: The overdue invoice.
            days_overdue: Number of days past the due date.

        Returns:
            Daily rate multiplied by days overdue.
        """
        if days_overdue <= 0:
            return 0.0
        return self._daily_rate * days_overdue


class PercentagePenalty(PenaltyStrategy):
    """Percentage-based penalty: percentage of base amount per day.

    Attributes:
        daily_percentage: Percentage of base amount charged per day (e.g., 0.01 = 1%).
    """

    def __init__(self, daily_percentage: float = 0.01) -> None:
        """Initialize with a daily percentage rate.

        Args:
            daily_percentage: Fraction of base amount per day. Defaults to 0.01 (1%).
        """
        self._daily_percentage = daily_percentage

    @property
    def daily_percentage(self) -> float:
        """Get the daily percentage rate."""
        return self._daily_percentage

    def calculate(self, invoice: Invoice, days_overdue: int) -> float:
        """Calculate percentage-based penalty.

        Args:
            invoice: The overdue invoice.
            days_overdue: Number of days past the due date.

        Returns:
            Base amount * daily percentage * days overdue.
        """
        if days_overdue <= 0:
            return 0.0
        return invoice.base_amount * self._daily_percentage * days_overdue


class ProgressivePenalty(PenaltyStrategy):
    """Progressive penalty with escalating tiers.

    Tiers:
    - Days 1-7:   tier1_rate per day (default 1%)
    - Days 8-30:  tier2_rate per day (default 2%)
    - Days 31+:   tier3_rate per day (default 5%)
    """

    def __init__(
        self,
        tier1_rate: float = 0.01,
        tier2_rate: float = 0.02,
        tier3_rate: float = 0.05,
    ) -> None:
        """Initialize with three penalty tier rates.

        Args:
            tier1_rate: Rate for days 1-7. Defaults to 0.01 (1%).
            tier2_rate: Rate for days 8-30. Defaults to 0.02 (2%).
            tier3_rate: Rate for days 31+. Defaults to 0.05 (5%).
        """
        self._tier1_rate = tier1_rate
        self._tier2_rate = tier2_rate
        self._tier3_rate = tier3_rate

    @property
    def tier1_rate(self) -> float:
        """Get the tier 1 penalty rate."""
        return self._tier1_rate

    @property
    def tier2_rate(self) -> float:
        """Get the tier 2 penalty rate."""
        return self._tier2_rate

    @property
    def tier3_rate(self) -> float:
        """Get the tier 3 penalty rate."""
        return self._tier3_rate

    def calculate(self, invoice: Invoice, days_overdue: int) -> float:
        """Calculate progressive penalty with escalating tiers.

        Args:
            invoice: The overdue invoice.
            days_overdue: Number of days past the due date.

        Returns:
            Total penalty across all applicable tiers.
        """
        if days_overdue <= 0:
            return 0.0

        base = invoice.base_amount
        penalty = 0.0

        # Tier 1: days 1-7
        tier1_days = min(days_overdue, 7)
        penalty += base * self._tier1_rate * tier1_days

        # Tier 2: days 8-30
        if days_overdue > 7:
            tier2_days = min(days_overdue - 7, 23)
            penalty += base * self._tier2_rate * tier2_days

        # Tier 3: days 31+
        if days_overdue > 30:
            tier3_days = days_overdue - 30
            penalty += base * self._tier3_rate * tier3_days

        return round(penalty, 2)
