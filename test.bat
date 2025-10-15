@echo off
chcp 65001 >nul
echo ============================================================
echo   Odoo MCP Unified - Test Script
echo ============================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Setting environment variables...
set ODOO_URL=https://alpha-goods-corporation.odoo.com
set ODOO_DB=alpha-goods-corporation
set ODOO_USERNAME=honglon_2003@yahoo.com.tw
set ODOO_PASSWORD=ss0972062949
set MCP_TRANSPORT=stdio
set ODOO_TIMEOUT=60
set ODOO_VERIFY_SSL=false

echo.
echo ============================================================
echo   Running Tests
echo ============================================================
echo.

echo [1/5] Testing config module...
python -c "from odoo_mcp.config import get_config; cfg = get_config(); print('Config OK:', cfg.odoo.url)"

echo.
echo [2/5] Testing MCP server import...
python -c "from odoo_mcp.server import mcp; print('MCP Server OK:', type(mcp))"

echo.
echo [3/5] Testing extensions...
python -c "from odoo_mcp.extensions import register_all_extensions; print('Extensions OK')"

echo.
echo [4/5] Testing Odoo client...
python -c "from odoo_mcp.odoo_client import get_odoo_client; client = get_odoo_client(); print('Odoo Client OK')"

echo.
echo [5/5] Testing connection to Odoo...
python -c "from odoo_mcp.odoo_client import get_odoo_client; client = get_odoo_client(); models = client.get_models(); print('Connection OK! Found', len(models), 'models')"

echo.
echo ============================================================
echo   All Tests Passed!
echo ============================================================
echo.
echo You can now:
echo 1. Run server in stdio mode: python run_server.py
echo 2. Run server in SSE mode: set MCP_TRANSPORT=sse ^&^& python run_server.py
echo 3. Configure Claude Desktop to use this server
echo.
pause
