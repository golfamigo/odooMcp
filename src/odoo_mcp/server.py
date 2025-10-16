"""
Unified Odoo MCP Server - Latest FastMCP API
Provides comprehensive Odoo ERP integration with 17+ tools
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP  # Use standalone fastmcp package, not mcp.server.fastmcp
from pydantic import BaseModel, Field

from .odoo_client import OdooClient, get_odoo_client
from .extensions import register_all_extensions


# Create MCP server using latest FastMCP API
# No lifespan needed - we use dependency injection instead
mcp = FastMCP(
    name="Odoo MCP Unified",
    instructions="""
    This server provides comprehensive Odoo ERP integration with 15+ tools.

    Core Tools:
    - execute_method: Execute any Odoo method (most powerful)
    - search_employee: Search for employees
    - search_holidays: Search for holidays/time-off

    Business Tools:
    - Sales: search_sales_orders, create_sales_order, analyze_sales_performance
    - Purchase: search_purchase_orders, create_purchase_order, analyze_supplier_performance
    - Inventory: check_product_availability, create_inventory_adjustment, analyze_inventory_turnover
    - Accounting: search_journal_entries, create_journal_entry, analyze_financial_ratios

    Note: MCP Resources disabled for N8N to reduce token usage. Use execute_method for all queries.
    """
)


# Helper function to get Odoo client (used by all tools)
def _get_odoo() -> OdooClient:
    """Get Odoo client instance"""
    return get_odoo_client()


# ----- MCP Resources -----
# NOTE: Resources are disabled for N8N integration to reduce token usage
# N8N MCP Client would preload all resource data, causing 2M+ token overflow
# All functionality is still available through MCP Tools (execute_method, etc.)

# @mcp.resource("odoo://models")
# def get_models() -> str:
#     """Disabled to reduce token usage in N8N"""
#     pass

# @mcp.resource("odoo://model/{model_name}")
# def get_model_info(model_name: str) -> str:
#     """Disabled to reduce token usage in N8N"""
#     pass

# @mcp.resource("odoo://record/{model_name}/{record_id}")
# def get_record(model_name: str, record_id: str) -> str:
#     """Disabled to reduce token usage in N8N"""
#     pass

# @mcp.resource("odoo://search/{model_name}/{domain}")
# def search_records_resource(model_name: str, domain: str) -> str:
#     """Disabled to reduce token usage in N8N"""
#     pass


# ----- Pydantic models for type safety -----


class DomainCondition(BaseModel):
    """A single condition in a search domain"""

    field: str = Field(description="Field name to search")
    operator: str = Field(
        description="Operator (e.g., '=', '!=', '>', '<', 'in', 'not in', 'like', 'ilike')"
    )
    value: Any = Field(description="Value to compare against")

    def to_tuple(self) -> List:
        """Convert to Odoo domain condition tuple"""
        return [self.field, self.operator, self.value]


class SearchDomain(BaseModel):
    """Search domain for Odoo models"""

    conditions: List[DomainCondition] = Field(
        default_factory=list,
        description="List of conditions for searching. All conditions are combined with AND operator.",
    )

    def to_domain_list(self) -> List[List]:
        """Convert to Odoo domain list format"""
        return [condition.to_tuple() for condition in self.conditions]


class EmployeeSearchResult(BaseModel):
    """Represents a single employee search result."""

    id: int = Field(description="Employee ID")
    name: str = Field(description="Employee name")


class SearchEmployeeResponse(BaseModel):
    """Response model for the search_employee tool."""

    success: bool = Field(description="Indicates if the search was successful")
    result: Optional[List[EmployeeSearchResult]] = Field(
        default=None, description="List of employee search results"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class Holiday(BaseModel):
    """Represents a single holiday."""

    display_name: str = Field(description="Display name of the holiday")
    start_datetime: str = Field(description="Start date and time of the holiday")
    stop_datetime: str = Field(description="End date and time of the holiday")
    employee_id: List[Union[int, str]] = Field(
        description="Employee ID associated with the holiday"
    )
    name: str = Field(description="Name of the holiday")
    state: str = Field(description="State of the holiday")


class SearchHolidaysResponse(BaseModel):
    """Response model for the search_holidays tool."""

    success: bool = Field(description="Indicates if the search was successful")
    result: Optional[List[Holiday]] = Field(
        default=None, description="List of holidays found"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


# ----- MCP Tools -----


@mcp.tool(description="Execute a custom method on an Odoo model using keyword arguments")
def execute_method(
    model: str = Field(description="The Odoo model name (e.g., 'res.partner')"),
    method: str = Field(description="Method name to execute (e.g., 'search_read')"),
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments for the method (e.g., {'domain': [], 'fields': ['name'], 'limit': 10})"
    ),
) -> Dict[str, Any]:
    """
    Execute a custom method on an Odoo model

    Parameters:
        model: The model name (e.g., 'res.partner')
        method: Method name to execute
        kwargs: Keyword arguments (dictionary)

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - result: Result of the method (if success)
        - error: Error message (if failure)

    Examples:
        search_read: kwargs={'domain': [], 'fields': ['name', 'email'], 'limit': 10}
        search: kwargs={'domain': [['name', 'ilike', 'test']], 'limit': 5}
        create: kwargs={'name': 'New Record', 'email': 'test@example.com'}
    """
    odoo = _get_odoo()
    try:
        # Apply safe defaults for search methods to prevent token overflow
        # N8N AI Agent often doesn't set limit/fields, causing 2M+ token responses
        if method in ['search_read', 'search']:
            # Set default limit if not specified
            if 'limit' not in kwargs:
                kwargs['limit'] = 100  # Default: max 100 records

            # For search_read, ensure reasonable field limit
            if method == 'search_read':
                # If fields is empty list or not set, limit to essential fields
                if not kwargs.get('fields'):
                    # Default essential fields for most models
                    kwargs['fields'] = ['id', 'name', 'display_name', 'create_date', 'write_date']

        # Execute method with kwargs only (no positional args)
        result = odoo.execute_method(model, method, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool(description="Search for employees by name")
def search_employee(
    name: str,
    limit: int = 20,
) -> SearchEmployeeResponse:
    """
    Search for employees by name using Odoo's name_search method.

    Parameters:
        name: The name (or part of the name) to search for.
        limit: The maximum number of results to return (default 20).

    Returns:
        SearchEmployeeResponse containing results or error information.
    """
    odoo = _get_odoo()
    model = "hr.employee"
    method = "name_search"

    args = []
    kwargs = {"name": name, "limit": limit}

    try:
        result = odoo.execute_method(model, method, *args, **kwargs)
        parsed_result = [
            EmployeeSearchResult(id=item[0], name=item[1]) for item in result
        ]
        return SearchEmployeeResponse(success=True, result=parsed_result)
    except Exception as e:
        return SearchEmployeeResponse(success=False, error=str(e))


@mcp.tool(description="Search for holidays within a date range")
def search_holidays(
    start_date: str,
    end_date: str,
    employee_id: Optional[int] = None,
) -> SearchHolidaysResponse:
    """
    Searches for holidays within a specified date range.

    Parameters:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        employee_id: Optional employee ID to filter holidays.

    Returns:
        SearchHolidaysResponse:  Object containing the search results.
    """
    odoo = _get_odoo()

    # Validate date format using datetime
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return SearchHolidaysResponse(
            success=False, error="Invalid start_date format. Use YYYY-MM-DD."
        )
    try:
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return SearchHolidaysResponse(
            success=False, error="Invalid end_date format. Use YYYY-MM-DD."
        )

    # Calculate adjusted start_date (subtract one day)
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    adjusted_start_date_dt = start_date_dt - timedelta(days=1)
    adjusted_start_date = adjusted_start_date_dt.strftime("%Y-%m-%d")

    # Build the domain
    domain = [
        "&",
        ["start_datetime", "<=", f"{end_date} 22:59:59"],
        # Use adjusted date
        ["stop_datetime", ">=", f"{adjusted_start_date} 23:00:00"],
    ]
    if employee_id:
        domain.append(
            ["employee_id", "=", employee_id],
        )

    try:
        holidays = odoo.search_read(
            model_name="hr.leave.report.calendar",
            domain=domain,
        )
        parsed_holidays = [Holiday(**holiday) for holiday in holidays]
        return SearchHolidaysResponse(success=True, result=parsed_holidays)

    except Exception as e:
        return SearchHolidaysResponse(success=False, error=str(e))


# Registrar todas las extensiones
register_all_extensions(mcp)
