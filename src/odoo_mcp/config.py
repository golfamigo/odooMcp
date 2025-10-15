"""
Unified Configuration Management for Odoo MCP Server
Type-safe configuration with validation
"""
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class OdooConfig:
    """Odoo connection configuration"""
    url: str
    database: str
    username: str
    password: str
    timeout: int = 60
    verify_ssl: bool = False

    def __post_init__(self):
        """Validate configuration"""
        if not self.url:
            raise ValueError("ODOO_URL is required")
        if not self.database:
            raise ValueError("ODOO_DB is required")
        if not self.username:
            raise ValueError("ODOO_USERNAME is required")
        if not self.password:
            raise ValueError("ODOO_PASSWORD is required")

        # Ensure URL doesn't end with slash
        self.url = self.url.rstrip('/')

    @classmethod
    def from_env(cls) -> "OdooConfig":
        """Load configuration from environment variables"""
        return cls(
            url=os.getenv("ODOO_URL", ""),
            database=os.getenv("ODOO_DB", ""),
            username=os.getenv("ODOO_USERNAME", ""),
            password=os.getenv("ODOO_PASSWORD", ""),
            timeout=int(os.getenv("ODOO_TIMEOUT", "60")),
            verify_ssl=os.getenv("ODOO_VERIFY_SSL", "false").lower() == "true"
        )

    @classmethod
    def from_json(cls, file_path: str) -> "OdooConfig":
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert to dictionary (without password)"""
        return {
            "url": self.url,
            "database": self.database,
            "username": self.username,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl
        }


@dataclass
class MCPConfig:
    """MCP Server configuration"""
    transport: str = "stdio"  # stdio or sse
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Load configuration from environment variables"""
        return cls(
            transport=os.getenv("MCP_TRANSPORT", "stdio"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )


@dataclass
class UnifiedConfig:
    """Unified configuration for the entire MCP server"""
    odoo: OdooConfig
    mcp: MCPConfig

    @classmethod
    def from_env(cls) -> "UnifiedConfig":
        """Load all configuration from environment variables"""
        return cls(
            odoo=OdooConfig.from_env(),
            mcp=MCPConfig.from_env()
        )

    @classmethod
    def from_json(cls, file_path: str) -> "UnifiedConfig":
        """Load all configuration from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        return cls(
            odoo=OdooConfig(**data.get("odoo", {})),
            mcp=MCPConfig(**data.get("mcp", {}))
        )

    def validate(self) -> bool:
        """Validate entire configuration"""
        try:
            # OdooConfig validation happens in __post_init__
            if self.mcp.transport not in ["stdio", "sse"]:
                raise ValueError(f"Invalid transport: {self.mcp.transport}")
            if self.mcp.port < 1 or self.mcp.port > 65535:
                raise ValueError(f"Invalid port: {self.mcp.port}")
            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")


# Global configuration instance
_config: Optional[UnifiedConfig] = None


def get_config() -> UnifiedConfig:
    """Get global configuration instance (singleton)"""
    global _config
    if _config is None:
        # Try to load from JSON file first, fall back to environment
        config_file = os.getenv("MCP_CONFIG_FILE")
        if config_file and Path(config_file).exists():
            _config = UnifiedConfig.from_json(config_file)
        else:
            _config = UnifiedConfig.from_env()

        # Validate
        _config.validate()

    return _config


def reset_config():
    """Reset global configuration (useful for testing)"""
    global _config
    _config = None
