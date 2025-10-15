# Odoo MCP Unified Server 🚀

**Unified Odoo Model Context Protocol (MCP) Server** with dual transport support (stdio + SSE), enhanced business tools, and type-safe configuration management.

## ✨ Features

### 🔌 Dual Transport Support
- **stdio**: For Claude Desktop integration
- **SSE**: For web deployment (Zeabur, Railway, etc.) - **No Supergateway needed!**

### 🛠️ Complete Tool Set (17+ Tools)

#### Core Tools (3)
- `execute_method` - Execute any Odoo method (most powerful)
- `search_employee` - Search for employees
- `search_holidays` - Search for holidays/time-off

#### Sales Tools (3)
- `search_sales_orders` - Search sales orders
- `create_sales_order` - Create new sales order
- `analyze_sales_performance` - Analyze sales performance with trends

#### Purchase Tools (3)
- `search_purchase_orders` - Search purchase orders
- `create_purchase_order` - Create new purchase order
- `analyze_supplier_performance` - Analyze supplier on-time delivery

#### Inventory Tools (2)
- `get_stock_levels` - Get current stock levels
- `predict_stock_needs` - Predict future stock needs

#### Accounting Tools (2)
- `get_financial_summary` - Get financial overview
- `analyze_receivables` - Analyze accounts receivable

### 📦 Resources (4)
- `odoo://models` - List all available models
- `odoo://model/{model_name}` - Get model information
- `odoo://record/{model_name}/{record_id}` - Get specific record
- `odoo://search/{model_name}/{domain}` - Search records

### ⚙️ Configuration Management
- Type-safe configuration with Pydantic
- Support for environment variables and JSON config
- Validation on startup

## 🚀 Quick Start

### For Claude Desktop (stdio mode)

1. **Install**
```bash
cd E:\gitHub\odoo-mcp-unified
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

2. **Configure** - Add to Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "odoo-unified": {
      "command": "E:\\gitHub\\odoo-mcp-unified\\venv\\Scripts\\python.exe",
      "args": ["E:\\gitHub\\odoo-mcp-unified\\run_server.py"],
      "env": {
        "ODOO_URL": "https://alpha-goods-corporation.odoo.com",
        "ODOO_DB": "alpha-goods-corporation",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### For Zeabur Deployment (SSE mode)

1. **Connect GitHub repo to Zeabur**

2. **Set environment variables**:
```
ODOO_URL=https://your-company.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
MCP_TRANSPORT=sse
PORT=8000
```

3. **Deploy** - Zeabur will automatically:
   - Build using Dockerfile
   - Expose SSE endpoint at `/sse`
   - No Supergateway needed!

## 📋 Environment Variables

### Required
- `ODOO_URL` - Odoo instance URL
- `ODOO_DB` - Database name
- `ODOO_USERNAME` - Username
- `ODOO_PASSWORD` - Password

### Optional
- `MCP_TRANSPORT` - Transport mode: `stdio` or `sse` (default: `stdio`)
- `ODOO_TIMEOUT` - Request timeout in seconds (default: `60`)
- `ODOO_VERIFY_SSL` - Verify SSL certificates (default: `false`)
- `PORT` - Server port for SSE mode (default: `8000`)
- `HOST` - Server host for SSE mode (default: `0.0.0.0`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

## 📖 Usage Examples

### Execute Any Odoo Method
```python
# Get product.product records
execute_method(
    model="product.product",
    method="search_read",
    args=[],
    kwargs={"fields": ["name", "list_price"], "limit": 10}
)
```

### Analyze Sales Performance
```python
analyze_sales_performance(
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "group_by": "month"
    }
)
```

### Check Supplier Performance
```python
analyze_supplier_performance(
    params={
        "supplier_id": 123,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)
```

## 🏗️ Project Structure

```
odoo-mcp-unified/
├── src/odoo_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py              # Main MCP server
│   ├── config.py              # 🆕 Configuration management
│   ├── odoo_client.py         # Odoo XML-RPC client
│   ├── extensions.py          # Extension registration
│   ├── models.py              # Pydantic models
│   ├── prompts.py             # MCP prompts
│   ├── resources.py           # MCP resources
│   ├── tools_sales.py         # Sales tools
│   ├── tools_purchase.py      # Purchase tools
│   ├── tools_inventory.py     # Inventory tools
│   └── tools_accounting.py    # Accounting tools
├── run_server.py              # 🆕 Unified server runner (stdio + SSE)
├── requirements.txt           # Fixed FastMCP version
├── pyproject.toml
├── Dockerfile                 # 🆕 Zeabur-ready
└── README.md
```

## 🔧 Development

### Run Tests
```bash
pytest tests/
```

### Run Server Locally (stdio)
```bash
export ODOO_URL=https://your-company.odoo.com
export ODOO_DB=your-database
export ODOO_USERNAME=your-username
export ODOO_PASSWORD=your-password
python run_server.py
```

### Run Server Locally (SSE)
```bash
export MCP_TRANSPORT=sse
export PORT=8000
python run_server.py
# Access: http://localhost:8000/sse
```

## 🐛 Troubleshooting

### ✅ Using Latest Stable Versions
This project uses the **latest stable versions** of FastMCP (>=0.7.0) and MCP (>=1.0.0):
- Modern FastMCP API without deprecated parameters
- Enhanced performance and stability
- Latest features and improvements

### SSL Certificate Error
If you see SSL errors:
```bash
export ODOO_VERIFY_SSL=false
```

### Connection Timeout
Increase timeout:
```bash
export ODOO_TIMEOUT=120
```

## 📦 What's New in v2.0

### 🆕 Compared to odoo-mcp-improved
- ✅ SSE Transport support (Zeabur deployment without Supergateway)
- ✅ Unified config.py module (type-safe configuration)
- ✅ Dual transport mode in single codebase
- ✅ Enhanced documentation

### 🆕 Compared to mcp-odoo
- ✅ All basic features (execute_method, resources)
- ✅ 12+ additional business tools
- ✅ Extension system
- ✅ SSE support
- ✅ Better error handling

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 🔗 Links

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Odoo Documentation](https://www.odoo.com/documentation/)
- [FastMCP](https://github.com/jlowin/fastmcp)

---

**Made with ❤️ for Alpha Goods Corporation**
