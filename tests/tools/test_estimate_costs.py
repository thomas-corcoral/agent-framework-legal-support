"""Tests for the estimate_costs tool."""

import pytest

from legal_support.tools.estimate_costs import (
    Canton,
    CostBreakdown,
    CostEstimationResult,
    CourtLevel,
    ProceedingType,
    estimate_costs,
    get_free_proceedings,
)


class TestProceedingType:
    """Tests for ProceedingType enum."""

    def test_civil_proceeding_type(self) -> None:
        """Test civil proceeding type."""
        assert ProceedingType.CIVIL.value == "civil"

    def test_labor_proceeding_type(self) -> None:
        """Test labor proceeding type."""
        assert ProceedingType.LABOR.value == "labor"

    def test_tenancy_proceeding_type(self) -> None:
        """Test tenancy proceeding type."""
        assert ProceedingType.TENANCY.value == "tenancy"

    def test_all_proceeding_types_have_values(self) -> None:
        """Test that all proceeding types have string values."""
        for pt in ProceedingType:
            assert isinstance(pt.value, str)
            assert len(pt.value) > 0


class TestCourtLevel:
    """Tests for CourtLevel enum."""

    def test_conciliation_level(self) -> None:
        """Test conciliation court level."""
        assert CourtLevel.CONCILIATION.value == "conciliation"

    def test_first_instance_level(self) -> None:
        """Test first instance court level."""
        assert CourtLevel.FIRST_INSTANCE.value == "first_instance"

    def test_cantonal_appeal_level(self) -> None:
        """Test cantonal appeal court level."""
        assert CourtLevel.CANTONAL_APPEAL.value == "cantonal_appeal"

    def test_federal_court_level(self) -> None:
        """Test federal court level."""
        assert CourtLevel.FEDERAL_COURT.value == "federal_court"


class TestCanton:
    """Tests for Canton enum."""

    def test_zurich_canton(self) -> None:
        """Test Zurich canton."""
        assert Canton.ZH.value == "ZH"

    def test_geneva_canton(self) -> None:
        """Test Geneva canton."""
        assert Canton.GE.value == "GE"

    def test_all_26_cantons_plus_federal(self) -> None:
        """Test that all 26 cantons plus federal are defined."""
        # 26 cantons + 1 FEDERAL = 27
        assert len(Canton) == 27


class TestCostBreakdown:
    """Tests for CostBreakdown model."""

    def test_cost_breakdown_creation(self) -> None:
        """Test creating a cost breakdown."""
        breakdown = CostBreakdown(
            court_fees=1000,
            attorney_fees_min=2000,
            attorney_fees_max=5000,
            expert_fees=500,
            other_costs=200,
            advance_payment=750,
        )
        assert breakdown.court_fees == 1000
        assert breakdown.attorney_fees_min == 2000
        assert breakdown.attorney_fees_max == 5000

    def test_total_min_calculation(self) -> None:
        """Test minimum total calculation."""
        breakdown = CostBreakdown(
            court_fees=1000,
            attorney_fees_min=2000,
            attorney_fees_max=5000,
            expert_fees=500,
            other_costs=200,
        )
        # total_min = court_fees + attorney_fees_min + expert_fees + other_costs  # noqa: ERA001
        assert breakdown.total_min == 1000 + 2000 + 500 + 200

    def test_total_max_calculation(self) -> None:
        """Test maximum total calculation."""
        breakdown = CostBreakdown(
            court_fees=1000,
            attorney_fees_min=2000,
            attorney_fees_max=5000,
            expert_fees=500,
            other_costs=200,
        )
        # total_max = court_fees + attorney_fees_max + expert_fees + other_costs  # noqa: ERA001
        assert breakdown.total_max == 1000 + 5000 + 500 + 200

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        breakdown = CostBreakdown(
            court_fees=1000,
            attorney_fees_min=2000,
            attorney_fees_max=5000,
            is_swiss_language=True,  # This should be ignored (not a field)
        )
        assert breakdown.expert_fees == 0
        assert breakdown.other_costs == 0
        assert breakdown.advance_payment == 0

    def test_negative_fees_rejected(self) -> None:
        """Test that negative fees are rejected."""
        with pytest.raises(ValueError):
            CostBreakdown(
                court_fees=-100,  # Invalid
                attorney_fees_min=2000,
                attorney_fees_max=5000,
                is_swiss_language=True,
            )


class TestCostEstimationResult:
    """Tests for CostEstimationResult model."""

    def test_result_creation(self) -> None:
        """Test creating a cost estimation result."""
        breakdown = CostBreakdown(
            court_fees=1000,
            attorney_fees_min=2000,
            attorney_fees_max=5000,
        )
        result = CostEstimationResult(
            proceeding_type=ProceedingType.CIVIL,
            court_level=CourtLevel.FIRST_INSTANCE,
            canton=Canton.ZH,
            value_in_dispute=50000,
            cost_breakdown=breakdown,
            legal_aid_eligible=False,
        )
        assert result.proceeding_type == ProceedingType.CIVIL
        assert result.value_in_dispute == 50000

    def test_total_estimate_range_format(self) -> None:
        """Test the formatted total estimate range."""
        breakdown = CostBreakdown(
            court_fees=1000,
            attorney_fees_min=2000,
            attorney_fees_max=5000,
        )
        result = CostEstimationResult(
            proceeding_type=ProceedingType.CIVIL,
            court_level=CourtLevel.FIRST_INSTANCE,
            canton=Canton.ZH,
            value_in_dispute=50000,
            cost_breakdown=breakdown,
            legal_aid_eligible=False,
        )
        # Should be formatted as "CHF X - Y"
        assert "CHF" in result.total_estimate_range
        assert "-" in result.total_estimate_range


class TestEstimateCosts:
    """Tests for the estimate_costs function."""

    def test_civil_proceeding_first_instance(self) -> None:
        """Test cost estimation for civil proceeding at first instance."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            court_level=CourtLevel.FIRST_INSTANCE,
            canton=Canton.ZH,
        )
        assert result.proceeding_type == ProceedingType.CIVIL
        assert result.court_level == CourtLevel.FIRST_INSTANCE
        assert result.cost_breakdown.court_fees > 0
        assert result.cost_breakdown.attorney_fees_min > 0
        assert result.cost_breakdown.attorney_fees_max > result.cost_breakdown.attorney_fees_min

    def test_labor_dispute_under_30k_free(self) -> None:
        """Test that labor disputes under 30k have no court fees."""
        result = estimate_costs(
            proceeding_type=ProceedingType.LABOR,
            value_in_dispute=25000,
            court_level=CourtLevel.FIRST_INSTANCE,
        )
        assert result.cost_breakdown.court_fees == 0
        # Should have a note about free labor disputes
        assert any("30,000" in note or "30000" in note for note in result.notes)

    def test_labor_dispute_over_30k_has_fees(self) -> None:
        """Test that labor disputes over 30k have court fees."""
        result = estimate_costs(
            proceeding_type=ProceedingType.LABOR,
            value_in_dispute=50000,
            court_level=CourtLevel.FIRST_INSTANCE,
        )
        assert result.cost_breakdown.court_fees > 0

    def test_tenancy_conciliation_free(self) -> None:
        """Test that tenancy conciliation is free."""
        result = estimate_costs(
            proceeding_type=ProceedingType.TENANCY,
            value_in_dispute=10000,
            court_level=CourtLevel.CONCILIATION,
        )
        assert result.cost_breakdown.court_fees == 0

    def test_higher_value_increases_fees(self) -> None:
        """Test that higher value in dispute increases fees."""
        result_low = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=10000,
            court_level=CourtLevel.FIRST_INSTANCE,
        )
        result_high = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=100000,
            court_level=CourtLevel.FIRST_INSTANCE,
        )
        assert result_high.cost_breakdown.court_fees > result_low.cost_breakdown.court_fees

    def test_appeal_level_increases_fees(self) -> None:
        """Test that appeal level increases fees."""
        result_first = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            court_level=CourtLevel.FIRST_INSTANCE,
        )
        result_appeal = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            court_level=CourtLevel.CANTONAL_APPEAL,
        )
        assert result_appeal.cost_breakdown.court_fees > result_first.cost_breakdown.court_fees

    def test_without_attorney_fees(self) -> None:
        """Test estimation without attorney fees."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            include_attorney=False,
        )
        assert result.cost_breakdown.attorney_fees_min == 0
        assert result.cost_breakdown.attorney_fees_max == 0

    def test_legal_aid_eligibility_low_income(self) -> None:
        """Test legal aid eligibility for low income."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            monthly_income=2000,  # Below threshold
        )
        assert result.legal_aid_eligible is True

    def test_legal_aid_not_eligible_high_income(self) -> None:
        """Test legal aid not eligible for high income."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            monthly_income=10000,  # Above threshold
        )
        assert result.legal_aid_eligible is False

    def test_advance_payment_calculated(self) -> None:
        """Test that advance payment is calculated."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
        )
        assert result.cost_breakdown.advance_payment > 0

    def test_federal_court_note_included(self) -> None:
        """Test that Federal Court includes specific notes."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
            court_level=CourtLevel.FEDERAL_COURT,
        )
        assert any("Federal Court" in note or "BGG" in note for note in result.notes)

    def test_criminal_proceeding(self) -> None:
        """Test criminal proceeding estimation."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CRIMINAL,
            value_in_dispute=0,
        )
        # Criminal prosecution costs are borne by state
        assert result.cost_breakdown.court_fees == 0
        assert any("state" in note.lower() for note in result.notes)

    def test_mediation_free_court_fees(self) -> None:
        """Test that mediation has no court fees."""
        result = estimate_costs(
            proceeding_type=ProceedingType.MEDIATION,
            value_in_dispute=20000,
        )
        assert result.cost_breakdown.court_fees == 0

    def test_family_proceeding(self) -> None:
        """Test family proceeding estimation."""
        result = estimate_costs(
            proceeding_type=ProceedingType.FAMILY,
            value_in_dispute=50000,
        )
        assert result.cost_breakdown.court_fees > 0
        assert any("family" in note.lower() for note in result.notes)

    def test_notes_always_include_disclaimer(self) -> None:
        """Test that notes always include a disclaimer."""
        result = estimate_costs(
            proceeding_type=ProceedingType.CIVIL,
            value_in_dispute=50000,
        )
        assert any("estimate" in note.lower() for note in result.notes)


class TestGetFreeProceedings:
    """Tests for the get_free_proceedings function."""

    def test_returns_list(self) -> None:
        """Test that function returns a list."""
        result = get_free_proceedings()
        assert isinstance(result, list)

    def test_list_not_empty(self) -> None:
        """Test that list is not empty."""
        result = get_free_proceedings()
        assert len(result) > 0

    def test_entries_have_required_fields(self) -> None:
        """Test that each entry has required fields."""
        result = get_free_proceedings()
        for entry in result:
            assert "type" in entry
            assert "legal_basis" in entry
            assert "description" in entry

    def test_includes_labor_disputes(self) -> None:
        """Test that labor disputes under 30k are included."""
        result = get_free_proceedings()
        labor_entry = next(
            (e for e in result if "labor" in e["type"].lower() or "30,000" in e["type"]),
            None,
        )
        assert labor_entry is not None

    def test_includes_legal_aid(self) -> None:
        """Test that legal aid is included."""
        result = get_free_proceedings()
        legal_aid_entry = next(
            (
                e
                for e in result
                if "legal aid" in e["type"].lower() or "unentgeltliche" in e["type"].lower()
            ),
            None,
        )
        assert legal_aid_entry is not None
