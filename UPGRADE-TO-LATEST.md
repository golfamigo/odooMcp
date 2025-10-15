# Upgrade to Latest FastMCP Versions 🚀

## Summary

This Odoo MCP Unified server now uses **the latest stable versions** of FastMCP and MCP libraries, not the outdated 0.1.0 version.

## What Changed

### Before (Old Approach - Deprecated)
```python
# Old way with deprecated parameters
mcp = FastMCP(
    "Server Name",
    description="...",      # ❌ No longer supported
    dependencies=["..."],    # ❌ Moved to config
    lifespan=app_lifespan,  # ❌ Different approach now
)

@mcp.tool
def my_tool(ctx: Context, param: str):
    odoo = ctx.request_context.lifespan_context.odoo  # ❌ Complex
```

### After (New Approach - Latest API)
```python
# Modern FastMCP API
mcp = FastMCP(
    name="Server Name",     # ✅ Simple name parameter
    instructions="""..."""  # ✅ Instructions instead of description
)

# Helper function for dependency management
def _get_odoo() -> OdooClient:
    return get_odoo_client()

@mcp.tool
def my_tool(param: str):    # ✅ No ctx needed for simple cases
    odoo = _get_odoo()       # ✅ Clean dependency injection
```

## Version Changes

### requirements.txt
```diff
# Before
- mcp>=0.1.1,<2.0.0
- fastmcp==0.1.0

# After
+ mcp>=1.0.0           # Latest stable
+ fastmcp>=0.7.0       # Latest stable
```

### Key Improvements

1. **No More `description` Parameter**
   - Old: `FastMCP("name", description="...")`
   - New: `FastMCP(name="name", instructions="...")`

2. **No More `dependencies` Parameter**
   - Dependencies now managed via `pyproject.toml` or `fastmcp.json`

3. **No More `lifespan` in Constructor**
   - Lifespan management is now automatic
   - Use dependency injection patterns instead

4. **Simplified Context Usage**
   - No need for `ctx.request_context.lifespan_context`
   - Direct dependency access via helper functions

## Benefits of Latest Versions

### FastMCP >=0.7.0
- ✅ Cleaner, more Pythonic API
- ✅ Better performance
- ✅ Improved error messages
- ✅ Enhanced SSE transport support
- ✅ Better dependency management
- ✅ More stable and battle-tested

### MCP >=1.0.0
- ✅ Stable v1 API
- ✅ Better protocol compliance
- ✅ Enhanced features
- ✅ Long-term support

## Migration Steps

If you have an old Odoo MCP project:

### 1. Update requirements.txt
```bash
# Replace old versions
mcp>=1.0.0
fastmcp>=0.7.0
```

### 2. Update FastMCP initialization
```python
# Old
mcp = FastMCP("Name", description="...", dependencies=[...], lifespan=...)

# New
mcp = FastMCP(name="Name", instructions="...")
```

### 3. Remove lifespan context access
```python
# Old
odoo = ctx.request_context.lifespan_context.odoo

# New
odoo = _get_odoo()  # Use helper function
```

### 4. Simplify tool signatures
```python
# Old - Complex
@mcp.tool
def my_tool(ctx: Context, param: str):
    odoo = ctx.request_context.lifespan_context.odoo
    ...

# New - Simple
@mcp.tool
def my_tool(param: str):
    odoo = _get_odoo()
    ...
```

### 5. Test thoroughly
```bash
cd your-project
pip install -r requirements.txt --upgrade
python run_server.py
```

## Compatibility

- ✅ Python 3.10+
- ✅ Claude Desktop (stdio transport)
- ✅ Zeabur/Railway (SSE transport)
- ✅ All existing tools and resources
- ✅ All business logic unchanged

## Why Not Lock to Old Versions?

### Problems with Old Approach (fastmcp==0.1.0)
- ❌ Using deprecated API
- ❌ Missing newer features
- ❌ Potential security issues
- ❌ No future updates
- ❌ Community moving forward

### Benefits of Latest Stable
- ✅ Active development
- ✅ Bug fixes and improvements
- ✅ Security updates
- ✅ Community support
- ✅ Better documentation

## Testing

After upgrading, test these scenarios:

### 1. Basic Connection
```bash
# Set environment variables
export ODOO_URL=https://your-company.odoo.com
export ODOO_DB=your-database
export ODOO_USERNAME=your-username
export ODOO_PASSWORD=your-password

# Run server
python run_server.py
```

### 2. Test execute_method
```python
# Should work without ctx
execute_method(
    model="res.partner",
    method="search_read",
    args=[],
    kwargs={"limit": 5}
)
```

### 3. Test all resources
```
odoo://models
odoo://model/res.partner
odoo://record/res.partner/1
odoo://search/res.partner/[[]]
```

## Rollback (If Needed)

If you encounter issues:

```bash
# Temporarily roll back
pip install "mcp>=0.1.1,<2.0.0" "fastmcp==0.1.0"

# Then report the issue!
```

But note: The old API will eventually be completely deprecated.

## Support

- 📖 [FastMCP Documentation](https://gofastmcp.com)
- 📖 [MCP Protocol](https://modelcontextprotocol.io)
- 💬 [GitHub Issues](https://github.com/jlowin/fastmcp/issues)

## Conclusion

This upgrade ensures your Odoo MCP server uses **modern, stable, and actively maintained** versions of FastMCP and MCP libraries. The changes are minimal but important for long-term maintainability and compatibility.

---

**Updated**: 2025-10-15
**Version**: 2.0.0 (Latest Stable)
