"""Unit tests for Strategy Pattern (Penalty Calculation)."""
from src.services.penalty_strategy import (
    FlatRatePenalty,
    PercentagePenalty,
    ProgressivePenalty,
)
from tests.conftest import make_invoice


class TestFlatRatePenalty:
    def test_zero_days(self):
        s = FlatRatePenalty(10.0)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 0) == 0.0

    def test_negative_days(self):
        s = FlatRatePenalty(10.0)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, -5) == 0.0

    def test_one_day(self):
        s = FlatRatePenalty(10.0)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 1) == 10.0

    def test_multiple_days(self):
        s = FlatRatePenalty(10.0)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 15) == 150.0

    def test_custom_rate(self):
        s = FlatRatePenalty(25.0)
        inv = make_invoice(base_amount=500.0)
        assert s.calculate(inv, 10) == 250.0

    def test_daily_rate_property(self):
        s = FlatRatePenalty(15.0)
        assert s.daily_rate == 15.0


class TestPercentagePenalty:
    def test_zero_days(self):
        s = PercentagePenalty(0.01)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 0) == 0.0

    def test_one_day_one_percent(self):
        s = PercentagePenalty(0.01)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 1) == 10.0

    def test_ten_days(self):
        s = PercentagePenalty(0.01)
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 10) == 100.0

    def test_custom_percentage(self):
        s = PercentagePenalty(0.05)
        inv = make_invoice(base_amount=2000.0)
        assert s.calculate(inv, 3) == 300.0

    def test_daily_percentage_property(self):
        s = PercentagePenalty(0.02)
        assert s.daily_percentage == 0.02


class TestProgressivePenalty:
    def test_zero_days(self):
        s = ProgressivePenalty()
        inv = make_invoice(base_amount=1000.0)
        assert s.calculate(inv, 0) == 0.0

    def test_tier1_only(self):
        s = ProgressivePenalty(tier1_rate=0.01)
        inv = make_invoice(base_amount=1000.0)
        # 5 days * 1% * 1000 = 50
        assert s.calculate(inv, 5) == 50.0

    def test_tier1_full(self):
        s = ProgressivePenalty(tier1_rate=0.01)
        inv = make_invoice(base_amount=1000.0)
        # 7 days * 1% * 1000 = 70
        assert s.calculate(inv, 7) == 70.0

    def test_tier1_and_tier2(self):
        s = ProgressivePenalty(tier1_rate=0.01, tier2_rate=0.02)
        inv = make_invoice(base_amount=1000.0)
        # 7*0.01*1000 + 3*0.02*1000 = 70 + 60 = 130
        assert s.calculate(inv, 10) == 130.0

    def test_all_three_tiers(self):
        s = ProgressivePenalty(tier1_rate=0.01, tier2_rate=0.02, tier3_rate=0.05)
        inv = make_invoice(base_amount=1000.0)
        # 7*0.01*1000 + 23*0.02*1000 + 5*0.05*1000 = 70 + 460 + 250 = 780
        assert s.calculate(inv, 35) == 780.0

    def test_tier_properties(self):
        s = ProgressivePenalty(0.01, 0.02, 0.05)
        assert s.tier1_rate == 0.01
        assert s.tier2_rate == 0.02
        assert s.tier3_rate == 0.05

    def test_large_overdue(self):
        s = ProgressivePenalty(tier1_rate=0.01, tier2_rate=0.02, tier3_rate=0.05)
        inv = make_invoice(base_amount=1000.0)
        # 7*10 + 23*20 + 70*50 = 70 + 460 + 3500 = 4030
        assert s.calculate(inv, 100) == 4030.0
