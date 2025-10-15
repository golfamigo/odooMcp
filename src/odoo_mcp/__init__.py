"""
Actualización del archivo __init__.py para incluir todos los módulos
"""

from . import odoo_client
from . import server
from . import models
from . import prompts
from . import tools_sales
from . import tools_purchase
from . import tools_inventory
from . import tools_accounting
from . import resources
from . import extensions

__all__ = [
    'odoo_client',
    'server',
    'models',
    'prompts',
    'tools_sales',
    'tools_purchase',
    'tools_inventory',
    'tools_accounting',
    'resources',
    'extensions'
]
