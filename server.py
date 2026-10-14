import sys
from mcp.server.mcpserver import MCPServer

# Initialize the new v2.x unified server object
server = MCPServer("My First MCP Server")

# ---------------------------------------------------------------------------
# 1. ADD A TOOL (v2.x registration pattern)
# ---------------------------------------------------------------------------
@server.tool()
def calculate_rv_spaces(total_acres: float, space_size_sqft: int = 1500) -> str:
    """
    Calculates the approximate layout capacity for an RV or mobile home park.
    
    :param total_acres: Total land area in acres.
    :param space_size_sqft: Average square footage allocated per lot (default 1500).
    """
    total_sqft = total_acres * 43560
    usable_sqft = total_sqft * 0.75
    estimated_spaces = int(usable_sqft // space_size_sqft)
    
    return (
        f"For a {total_acres}-acre parcel:\n"
        f"- Total Area: {total_sqft:,.0f} sq ft\n"
        f"- Usable Development Area (75% rule): {usable_sqft:,.0f} sq ft\n"
        f"- Estimated Layout Capacity: **{estimated_spaces} spaces** (at {space_size_sqft} sq ft per lot)."
    )

# ---------------------------------------------------------------------------
# 2. ADD A RESOURCE (v2.x registration pattern)
# ---------------------------------------------------------------------------
@server.resource("config://park-standards")
def get_park_standards() -> str:
    """Returns standard industry guidelines for utility and space layouts."""
    return (
        "Standard RV Park Specifications:\n"
        "- Back-in Spaces: Typically 12-15 feet wide by 40-50 feet long.\n"
        "- Pull-through Spaces: Typically 15-20 feet wide by 60-80 feet long.\n"
        "- Electrical Requirements: Standard layouts mix 20A, 30A, and 50A pedestals.\n"
        "- Water/Sewer: Utility lines require deep trenching isolated from electrical lines."
    )

# ---------------------------------------------------------------------------
# Execution Wrapper
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Start the server using standard I/O communication pipes
    server.run()

