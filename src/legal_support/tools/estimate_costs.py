"""Cost estimation tool for Swiss legal proceedings.

This module provides cost estimation functionality for various types of
Swiss legal proceedings, including court fees, attorney fees, and other
procedural costs.

Swiss legal costs vary based on:
- Type of proceeding (civil, criminal, administrative, labor)
- Value in dispute (Streitwert)
- Canton (different cantons have different fee schedules)
- Court level (first instance, appeal, federal)
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class ProceedingType(Enum):
    """Types of legal proceedings in Switzerland."""

    CIVIL = "civil"
    CRIMINAL = "criminal"
    ADMINISTRATIVE = "administrative"
    LABOR = "labor"
    TENANCY = "tenancy"
    FAMILY = "family"
    DEBT_COLLECTION = "debt_collection"
    BANKRUPTCY = "bankruptcy"
    MEDIATION = "mediation"


class CourtLevel(Enum):
    """Court levels in the Swiss judicial system."""

    CONCILIATION = "conciliation"  # Schlichtungsbehörde
    FIRST_INSTANCE = "first_instance"  # Bezirksgericht / Regionalgericht
    CANTONAL_APPEAL = "cantonal_appeal"  # Obergericht / Kantonsgericht
    FEDERAL_COURT = "federal_court"  # Bundesgericht


class Canton(Enum):
    """Swiss cantons for fee schedule lookup."""

    ZH = "ZH"  # Zurich
    BE = "BE"  # Bern
    LU = "LU"  # Lucerne
    UR = "UR"  # Uri
    SZ = "SZ"  # Schwyz
    OW = "OW"  # Obwalden
    NW = "NW"  # Nidwalden
    GL = "GL"  # Glarus
    ZG = "ZG"  # Zug
    FR = "FR"  # Fribourg
    SO = "SO"  # Solothurn
    BS = "BS"  # Basel-Stadt
    BL = "BL"  # Basel-Landschaft
    SH = "SH"  # Schaffhausen
    AR = "AR"  # Appenzell Ausserrhoden
    AI = "AI"  # Appenzell Innerrhoden
    SG = "SG"  # St. Gallen
    GR = "GR"  # Graubünden
    AG = "AG"  # Aargau
    TG = "TG"  # Thurgau
    TI = "TI"  # Ticino
    VD = "VD"  # Vaud
    VS = "VS"  # Valais
    NE = "NE"  # Neuchâtel
    GE = "GE"  # Geneva
    JU = "JU"  # Jura
    FEDERAL = "FEDERAL"  # Federal level


class CostBreakdown(BaseModel):
    """Detailed breakdown of estimated costs."""

    court_fees: float = Field(ge=0, description="Court fees (Gerichtsgebühren) in CHF")
    attorney_fees_min: float = Field(ge=0, description="Minimum estimated attorney fees in CHF")
    attorney_fees_max: float = Field(ge=0, description="Maximum estimated attorney fees in CHF")
    expert_fees: float = Field(default=0, ge=0, description="Estimated expert/witness fees in CHF")
    other_costs: float = Field(default=0, ge=0, description="Other procedural costs in CHF")
    advance_payment: float = Field(
        default=0, ge=0, description="Required advance payment (Kostenvorschuss) in CHF"
    )

    @property
    def total_min(self) -> float:
        """Minimum total estimated cost."""
        return self.court_fees + self.attorney_fees_min + self.expert_fees + self.other_costs

    @property
    def total_max(self) -> float:
        """Maximum total estimated cost."""
        return self.court_fees + self.attorney_fees_max + self.expert_fees + self.other_costs


class CostEstimationResult(BaseModel):
    """Result of a cost estimation for legal proceedings."""

    proceeding_type: ProceedingType = Field(description="Type of legal proceeding")
    court_level: CourtLevel = Field(description="Court level")
    canton: Canton = Field(description="Canton or federal level")
    value_in_dispute: float = Field(ge=0, description="Value in dispute (Streitwert) in CHF")
    cost_breakdown: CostBreakdown = Field(description="Detailed cost breakdown")
    legal_aid_eligible: bool = Field(
        description="Whether legal aid (unentgeltliche Rechtspflege) may be available"
    )
    notes: list[str] = Field(default_factory=list, description="Additional notes and disclaimers")

    @property
    def total_estimate_range(self) -> str:
        """Human-readable total cost estimate range."""
        return f"CHF {self.cost_breakdown.total_min:,.0f} - {self.cost_breakdown.total_max:,.0f}"


# Court fee schedules (simplified, based on typical Swiss cantonal rates)
# These are approximations - actual fees vary by canton and case specifics


def _get_conciliation_value(value_in_dispute):
    if value_in_dispute <= 2000:
        return 0
    elif value_in_dispute <= 10000:
        return 150
    elif value_in_dispute <= 30000:
        return 300
    else:
        return 500


def _calculate_civil_court_fees(value_in_dispute: float, court_level: CourtLevel) -> float:
    """Calculate civil court fees based on value in dispute.

    Based on typical Swiss fee schedules (Art. 96 ZPO / Gebührenverordnungen).
    Fees are generally progressive based on Streitwert.
    """
    if court_level == CourtLevel.CONCILIATION:
        # Schlichtungsbehörde: typically free or very low fees
        return _get_conciliation_value(value_in_dispute)

    # First instance and appeal courts use progressive scales
    base_fees = {
        CourtLevel.FIRST_INSTANCE: 1.0,
        CourtLevel.CANTONAL_APPEAL: 1.3,
        CourtLevel.FEDERAL_COURT: 1.5,
    }
    multiplier = base_fees.get(court_level, 1.0)

    # Progressive fee calculation (simplified Swiss model)
    if value_in_dispute <= 2000:
        base = 250
    elif value_in_dispute <= 5000:
        base = 500
    elif value_in_dispute <= 10000:
        base = 800
    elif value_in_dispute <= 20000:
        base = 1200
    elif value_in_dispute <= 30000:
        base = 1800
    elif value_in_dispute <= 50000:
        base = 2500
    elif value_in_dispute <= 100000:
        base = 4000
    elif value_in_dispute <= 200000:
        base = 6000
    elif value_in_dispute <= 500000:
        base = 10000
    elif value_in_dispute <= 1000000:
        base = 15000
    else:
        # For values over 1M, use percentage-based calculation
        base = 15000 + (value_in_dispute - 1000000) * 0.005
        base = min(base, 100000)  # Cap at 100k

    return base * multiplier


def _calculate_attorney_fees(
    value_in_dispute: float,
    proceeding_type: ProceedingType,
    court_level: CourtLevel,
) -> tuple[float, float]:
    """Calculate estimated attorney fee range.

    Based on typical Swiss attorney fee guidelines (Anwaltsgebührenverordnungen).
    Returns (min_fee, max_fee) tuple.
    """
    # Base hourly rates (CHF)
    hourly_rate_min = 250
    hourly_rate_max = 450

    # Estimated hours based on proceeding type and complexity
    hours_estimates = {
        (ProceedingType.CIVIL, CourtLevel.CONCILIATION): (2, 5),
        (ProceedingType.CIVIL, CourtLevel.FIRST_INSTANCE): (10, 40),
        (ProceedingType.CIVIL, CourtLevel.CANTONAL_APPEAL): (15, 50),
        (ProceedingType.CIVIL, CourtLevel.FEDERAL_COURT): (20, 60),
        (ProceedingType.LABOR, CourtLevel.CONCILIATION): (2, 5),
        (ProceedingType.LABOR, CourtLevel.FIRST_INSTANCE): (8, 30),
        (ProceedingType.TENANCY, CourtLevel.CONCILIATION): (2, 5),
        (ProceedingType.TENANCY, CourtLevel.FIRST_INSTANCE): (8, 25),
        (ProceedingType.FAMILY, CourtLevel.FIRST_INSTANCE): (10, 50),
        (ProceedingType.FAMILY, CourtLevel.CANTONAL_APPEAL): (15, 40),
        (ProceedingType.ADMINISTRATIVE, CourtLevel.FIRST_INSTANCE): (10, 40),
        (ProceedingType.DEBT_COLLECTION, CourtLevel.FIRST_INSTANCE): (5, 20),
        (ProceedingType.MEDIATION, CourtLevel.CONCILIATION): (3, 10),
    }

    key = (proceeding_type, court_level)
    hours_min, hours_max = hours_estimates.get(key, (10, 40))

    # Adjust for value in dispute (complex cases with higher stakes = more work)
    if value_in_dispute > 100000:
        hours_min = int(hours_min * 1.5)
        hours_max = int(hours_max * 1.5)
    elif value_in_dispute > 500000:
        hours_min = int(hours_min * 2)
        hours_max = int(hours_max * 2)

    return (hours_min * hourly_rate_min, hours_max * hourly_rate_max)


def _calculate_labor_court_fees(value_in_dispute: float, court_level: CourtLevel) -> float:
    """Calculate labor court fees.

    Labor disputes up to CHF 30,000 are typically free (Art. 113 ZPO).
    """
    if value_in_dispute <= 30000 and court_level != CourtLevel.FEDERAL_COURT:
        return 0
    return _calculate_civil_court_fees(value_in_dispute, court_level) * 0.5


def _calculate_tenancy_court_fees(value_in_dispute: float, court_level: CourtLevel) -> float:
    """Calculate tenancy court fees.

    Tenancy conciliation is typically free or very low cost.
    """
    if court_level == CourtLevel.CONCILIATION:
        return 0
    return _calculate_civil_court_fees(value_in_dispute, court_level) * 0.7


def _calculate_administrative_fees(court_level: CourtLevel) -> float:
    """Calculate administrative proceeding fees.

    Administrative proceedings have fixed fee ranges.
    """
    fees = {
        CourtLevel.FIRST_INSTANCE: 1500,
        CourtLevel.CANTONAL_APPEAL: 2500,
        CourtLevel.FEDERAL_COURT: 5000,
    }
    return fees.get(court_level, 1500)


def _calculate_criminal_fees() -> float:
    """Calculate criminal proceeding fees.

    Criminal defense costs are highly variable.
    This returns a typical first-instance estimate.
    """
    return 0  # Prosecution costs are borne by the state; defendant may have attorney fees


def estimate_costs(  # noqa: PLR0912
    proceeding_type: Annotated[ProceedingType, Field(description="Type of legal proceeding")],
    value_in_dispute: Annotated[
        float, Field(ge=0, description="Value in dispute (Streitwert) in CHF")
    ],
    court_level: Annotated[
        CourtLevel, Field(description="Court level")
    ] = CourtLevel.FIRST_INSTANCE,
    canton: Annotated[Canton, Field(description="Canton for fee schedule")] = Canton.ZH,
    include_attorney: Annotated[
        bool, Field(description="Whether to include attorney fee estimates")
    ] = True,
    monthly_income: Annotated[
        float | None, Field(description="Monthly income for legal aid eligibility check")
    ] = None,
) -> CostEstimationResult:
    """Estimate costs for Swiss legal proceedings.

    This function provides an estimate of the costs involved in various types
    of Swiss legal proceedings, including court fees, attorney fees, and
    other procedural costs.

    Args:
        proceeding_type: Type of legal proceeding (civil, labor, tenancy, etc.)
        value_in_dispute: Value in dispute (Streitwert) in CHF
        court_level: Court level (conciliation, first instance, appeal, federal)
        canton: Canton for fee schedule lookup
        include_attorney: Whether to include attorney fee estimates
        monthly_income: Monthly income for legal aid eligibility assessment

    Returns:
        CostEstimationResult with detailed cost breakdown and notes.

    Examples:
        >>> result = estimate_costs(
        ...     proceeding_type=ProceedingType.CIVIL,
        ...     value_in_dispute=50000,
        ...     court_level=CourtLevel.FIRST_INSTANCE,
        ...     canton=Canton.ZH,
        ... )
        >>> print(result.total_estimate_range)
        'CHF 5,000 - 20,500'

        >>> result = estimate_costs(
        ...     proceeding_type=ProceedingType.LABOR,
        ...     value_in_dispute=10000,
        ...     court_level=CourtLevel.FIRST_INSTANCE,
        ... )
        >>> result.cost_breakdown.court_fees
        0  # Free for labor disputes under 30k
    """
    notes: list[str] = []

    # Calculate court fees based on proceeding type
    if proceeding_type == ProceedingType.CIVIL:
        court_fees = _calculate_civil_court_fees(value_in_dispute, court_level)
    elif proceeding_type in (ProceedingType.LABOR,):
        court_fees = _calculate_labor_court_fees(value_in_dispute, court_level)
        if value_in_dispute <= 30000:
            notes.append(
                "Labor disputes up to CHF 30,000 are typically free of court fees (Art. 113 ZPO)."
            )
    elif proceeding_type == ProceedingType.TENANCY:
        court_fees = _calculate_tenancy_court_fees(value_in_dispute, court_level)
        if court_level == CourtLevel.CONCILIATION:
            notes.append("Tenancy conciliation (Schlichtungsbehörde) is typically free.")
    elif proceeding_type == ProceedingType.ADMINISTRATIVE:
        court_fees = _calculate_administrative_fees(court_level)
    elif proceeding_type == ProceedingType.CRIMINAL:
        court_fees = _calculate_criminal_fees()
        notes.append(
            "Criminal prosecution costs are borne by the state. "
            "Defense attorney fees may apply if you hire private counsel."
        )
    elif proceeding_type == ProceedingType.FAMILY:
        court_fees = _calculate_civil_court_fees(value_in_dispute, court_level) * 0.8
        notes.append("Family law proceedings may qualify for reduced fees or legal aid.")
    elif proceeding_type == ProceedingType.DEBT_COLLECTION:
        # Betreibung fees are fixed
        court_fees = min(500, value_in_dispute * 0.02)
    elif proceeding_type == ProceedingType.MEDIATION:
        court_fees = 0
        notes.append(
            "Mediation costs are typically shared between parties. "
            "Mediator fees: CHF 200-400 per hour."
        )
    else:
        court_fees = _calculate_civil_court_fees(value_in_dispute, court_level)

    # Calculate attorney fees if requested
    if include_attorney:
        attorney_min, attorney_max = _calculate_attorney_fees(
            value_in_dispute, proceeding_type, court_level
        )
    else:
        attorney_min, attorney_max = 0, 0

    # Calculate advance payment (typically 50-100% of expected court fees)
    advance_payment = court_fees * 0.75

    # Check legal aid eligibility
    legal_aid_eligible = False
    if monthly_income is not None:
        # Simplified legal aid eligibility check
        # Actual eligibility depends on assets, family situation, case merits
        income_threshold = 4000  # Approximate threshold
        if monthly_income <= income_threshold:
            legal_aid_eligible = True
            notes.append(
                "Based on your income, you may be eligible for legal aid "
                "(unentgeltliche Rechtspflege, Art. 117 ZPO). "
                "This could cover court fees and provide a free attorney."
            )

    # Add standard notes
    notes.append(
        "These are estimates only. Actual costs may vary based on case complexity, "
        "canton-specific fee schedules, and attorney rates."
    )

    if court_level == CourtLevel.FEDERAL_COURT:
        notes.append(
            "Federal Court fees are regulated by the Bundesgerichtsgesetz (BGG). "
            "Appeal to the Federal Court requires meeting specific value thresholds."
        )

    # Create cost breakdown
    cost_breakdown = CostBreakdown(
        court_fees=court_fees,
        attorney_fees_min=attorney_min,
        attorney_fees_max=attorney_max,
        expert_fees=0,  # Would need more info to estimate
        other_costs=200,  # Typical miscellaneous costs
        advance_payment=advance_payment,
    )

    return CostEstimationResult(
        proceeding_type=proceeding_type,
        court_level=court_level,
        canton=canton,
        value_in_dispute=value_in_dispute,
        cost_breakdown=cost_breakdown,
        legal_aid_eligible=legal_aid_eligible,
        notes=notes,
    )


def get_free_proceedings() -> list[dict[str, str]]:
    """Get a list of typically free legal proceedings in Switzerland.

    Returns:
        List of proceeding types that are typically free or have waived fees.
    """
    return [
        {
            "type": "Labor disputes up to CHF 30,000",
            "legal_basis": "Art. 113 ZPO",
            "description": "Court fees are waived for labor law disputes "
            "with a value in dispute up to CHF 30,000.",
        },
        {
            "type": "Tenancy conciliation",
            "legal_basis": "Art. 197 ZPO",
            "description": "Conciliation proceedings for rental disputes are "
            "typically free of charge.",
        },
        {
            "type": "Criminal victim assistance",
            "legal_basis": "Opferhilfegesetz (OHG)",
            "description": "Victims of crime can receive free legal assistance "
            "through victim support services.",
        },
        {
            "type": "Legal aid (unentgeltliche Rechtspflege)",
            "legal_basis": "Art. 117-123 ZPO",
            "description": "Parties with insufficient means can apply for "
            "court fee waivers and free legal representation.",
        },
        {
            "type": "Social insurance disputes",
            "legal_basis": "Art. 61 ATSG",
            "description": "First-instance proceedings in social insurance "
            "matters are typically free.",
        },
    ]
