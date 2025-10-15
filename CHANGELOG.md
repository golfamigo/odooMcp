# Changelog

All notable changes to Odoo MCP Unified will be documented in this file.

## [2.0.0] - 2025-10-15

### 🎉 Initial Unified Release

This is the first unified release combining the best features from multiple Odoo MCP implementations.

### ✨ Added

#### Core Features
- **Dual Transport Support**: Both stdio (Claude Desktop) and SSE (web deployment)
- **Unified Configuration**: Type-safe config.py module with validation
- **Complete Tool Set**: 17+ tools across sales, purchase, inventory, and accounting
- **All Resources**: 4 MCP resources for model exploration

#### New Features vs odoo-mcp-improved
- ✅ SSE Transport support for Zeabur deployment (no Supergateway needed)
- ✅ config.py unified configuration module
- ✅ Dual transport mode in single codebase
- ✅ Enhanced run_server.py with mode switching
- ✅ Complete documentation and examples

#### New Features vs mcp-odoo
- ✅ 12+ additional business tools
- ✅ Sales performance analysis
- ✅ Supplier performance tracking
- ✅ Stock prediction
- ✅ Financial reporting
- ✅ Extension system for modularity

### 🔧 Fixed
- Fixed FastMCP version compatibility (locked to 0.1.0)
- Improved error handling across all tools
- Enhanced logging for debugging

### 📦 Dependencies
- mcp >= 0.1.1, < 2.0.0
- fastmcp == 0.1.0 (fixed version)
- requests >= 2.31.0
- pypi-xmlrpc == 2020.12.3
- pydantic >= 2.0.0
- starlette >= 0.27.0 (for SSE)
- uvicorn[standard] >= 0.23.0 (for SSE)
- sse-starlette >= 1.6.5 (for SSE)
- python-dotenv >= 1.0.0

### 📚 Documentation
- Complete README with examples
- Installation and testing scripts
- Environment variable documentation
- Deployment guides for both modes

### 🏗️ Project Structure
```
odoo-mcp-unified/
├── src/odoo_mcp/          # All source code
│   ├── config.py          # 🆕 Configuration management
│   ├── server.py          # Main MCP server
│   ├── extensions.py      # Extension registration
│   └── tools_*.py         # Business tools
├── run_server.py          # 🆕 Unified runner (stdio + SSE)
├── requirements.txt       # Fixed dependencies
├── Dockerfile             # 🆕 Zeabur-ready
└── README.md              # Complete documentation
```

### 🎯 Use Cases
- Claude Desktop integration (stdio mode)
- Zeabur/Railway deployment (SSE mode)
- Sales performance tracking
- Supplier on-time delivery analysis
- Inventory management and prediction
- Financial reporting and receivables analysis

---

**Made with ❤️ for Alpha Goods Corporation**
