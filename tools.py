
import httpx  # Standard library for hitting external APIs like Rent Manager or Newbook
from mcp.server.mcpserver import Context, MCPServer


# ---------------------------------------------------------------------------
# MOCK API GATEWAY (Replace variables below with your real API endpoints/keys)
# ---------------------------------------------------------------------------
PARK_SYSTEM_URL = "https://newbook.cloud" # Or your Rent Manager Web API endpoint

def fetch_external_park_data(property_id: str, api_token: str | None) -> dict:
    """Helper function to fetch active operational metrics from the park system."""
    # This is structured to mimic live payload pulls for site states
    # In a real environment, you would use: response = httpx.get(..., headers={"Authorization": API_TOKEN})
    if not api_token:
        raise ValueError("Security Error: API Token is missing from the environment configuration.")
    mock_responses = {
        "101": {"park_name": "Tarrytown RV Oasis", "active_occupied_lots": 42, "base_electric_rate_kwh": 0.14},
        "102": {"park_name": "Austin Mobile Haven", "active_occupied_lots": 85, "base_electric_rate_kwh": 0.12}
    }
    return mock_responses.get(property_id, {"park_name": "Unknown Park", "active_occupied_lots": 0, "base_electric_rate_kwh": 0.15})

# ---------------------------------------------------------------------------
# 1. NEW TOOL: UTILITY COST ESTIMATOR (Tied to External API metrics)
# ---------------------------------------------------------------------------
def estimate_utility_costs(
    property_id: str,
    ctx: Context,
    avg_kwh_per_lot: float = 350.0,
    monthly_water_sewer_per_lot: float = 45.0,
) -> str:
    """
    Fetches occupancy data from the external park management system and estimates monthly utility overhead.
    
    :param property_id: Unique identifier for the park location (e.g., '101' or '102').
    :param avg_kwh_per_lot: Estimated average monthly Kilowatt-hour usage per active RV/Lot (default 350).
    :param monthly_water_sewer_per_lot: Flat fixed rate utility charge for city water/sewer metrics per lot.
    """
    # Fetch operational metrics straight from the API layer
    app_state = ctx.request_context.lifespan_context

    park_data = fetch_external_park_data(
        property_id,
        api_token=app_state["api_token"],
    )
    park_name = park_data["park_name"]
    occupied_lots = park_data["active_occupied_lots"]
    electric_rate = park_data["base_electric_rate_kwh"]
    
    if occupied_lots == 0:
        return f"Error: No active operational data or occupied slots found for Property ID '{property_id}'."

    # Calculation logic for utility footprint
    total_electric_cost = occupied_lots * avg_kwh_per_lot * electric_rate
    total_water_sewer_cost = occupied_lots * monthly_water_sewer_per_lot
    total_estimated_overhead = total_electric_cost + total_water_sewer_cost
    
    return (
        f"### Utility Cost Estimation: {park_name} (ID: {property_id})\n"
        f"**Live Metrics Sync:**\n"
        f"- Active Occupied Lots: **{occupied_lots} lots**\n"
        f"- Sourced Electric Rate: ${electric_rate:.2f} per kWh\n\n"
        f"**Estimated Breakdown (Monthly):**\n"
        f"- Electricity ({avg_kwh_per_lot} kWh/lot avg): ${total_electric_cost:,.2f}\n"
        f"- Water & Sewer (${monthly_water_sewer_per_lot}/lot flat): ${total_water_sewer_cost:,.2f}\n"
        f"---\n"
        f"Total Estimated Utility Operational Cost: **${total_estimated_overhead:,.2f}**"
    )

# ---------------------------------------------------------------------------
# 2. LEGACY TOOL: LAYOUT CALCULATOR
# ---------------------------------------------------------------------------
def calculate_rv_spaces(total_acres: float, space_size_sqft: int = 1500) -> str:
    """Calculates the approximate layout capacity for an RV or mobile home park."""
    total_sqft = total_acres * 43560
    usable_sqft = total_sqft * 0.75
    estimated_spaces = int(usable_sqft // space_size_sqft)
    return (
        f"For a {total_acres}-acre parcel:\n"
        f"- Total Area: {total_sqft:,.0f} sq ft\n"
        f"- Usable Development Area (75% rule): {usable_sqft:,.0f} sq ft\n"
        f"- Estimated Layout Capacity: **{estimated_spaces} spaces** (at {space_size_sqft} sq ft per lot)."
    )

def register_tools(server: MCPServer) -> None:
    """Register our functions as tools on the supplied server."""
    server.tool()(estimate_utility_costs)
    server.tool()(calculate_rv_spaces)
