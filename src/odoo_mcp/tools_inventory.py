"""
Implementación de herramientas (tools) para inventario en MCP-Odoo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastmcp import FastMCP

from .models import (
    ProductAvailabilityInput,
    InventoryAdjustmentCreate,
    InventoryTurnoverInput
)
from .odoo_client import get_odoo_client

def register_inventory_tools(mcp: FastMCP) -> None:
    """Registra herramientas relacionadas con inventario"""

    # Helper function to get Odoo client
    def _get_odoo():
        return get_odoo_client()

    @mcp.tool(description="Verifica la disponibilidad de stock para uno o más productos")
    def check_product_availability(
        product_ids: List[int],
        location_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verifica la disponibilidad de stock para uno o más productos

        Args:
            product_ids: Lista de IDs de productos a verificar
            location_id: ID de la ubicación específica (opcional)

        Returns:
            Diccionario con información de disponibilidad
        """
        odoo = _get_odoo()

        try:
            # Verificar que los productos existen
            products = odoo.search_read(
                "product.product",
                [("id", "in", product_ids)],
                fields=["name", "default_code", "type", "uom_id"]
            )

            if not products:
                return {"success": False, "error": "No se encontraron productos con los IDs proporcionados"}

            # Mapear IDs a nombres para referencia
            product_names = {p["id"]: p["name"] for p in products}

            # Obtener disponibilidad
            availability = {}

            for product_id in product_ids:
                # Construir contexto para la consulta
                context = {}
                if location_id:
                    context["location"] = location_id
                
                # Obtener cantidad disponible usando el método qty_available
                try:
                    product_data = odoo.execute_method(
                        "product.product", 
                        "read", 
                        [product_id], 
                        ["qty_available", "virtual_available", "incoming_qty", "outgoing_qty"],
                        context
                    )
                    
                    if product_data:
                        product_info = product_data[0]
                        availability[product_id] = {
                            "name": product_names.get(product_id, f"Producto {product_id}"),
                            "qty_available": product_info["qty_available"],
                            "virtual_available": product_info["virtual_available"],
                            "incoming_qty": product_info["incoming_qty"],
                            "outgoing_qty": product_info["outgoing_qty"]
                        }
                    else:
                        availability[product_id] = {
                            "name": product_names.get(product_id, f"Producto {product_id}"),
                            "error": "Producto no encontrado"
                        }
                except Exception as e:
                    availability[product_id] = {
                        "name": product_names.get(product_id, f"Producto {product_id}"),
                        "error": str(e)
                    }
            
            # Obtener información de la ubicación si se especificó
            location_info = None
            if location_id:
                try:
                    location_data = odoo.search_read(
                        "stock.location",
                        [("id", "=", location_id)],
                        fields=["name", "complete_name"]
                    )
                    if location_data:
                        location_info = location_data[0]
                except Exception:
                    location_info = {"id": location_id, "name": "Ubicación desconocida"}
            
            return {
                "success": True,
                "result": {
                    "products": availability,
                    "location": location_info
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Crea un ajuste de inventario para corregir el stock")
    def create_inventory_adjustment(
        name: str,
        adjustment_lines: List[Dict[str, Any]],
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un ajuste de inventario para corregir el stock

        Args:
            name: Nombre o descripción del ajuste
            adjustment_lines: Lista de líneas de ajuste. Cada línea debe tener:
                - product_id (int): ID del producto
                - location_id (int): ID de la ubicación
                - product_qty (float): Cantidad contada real
            date: Fecha del ajuste en formato YYYY-MM-DD (opcional)

        Returns:
            Respuesta con el resultado de la operación
        """
        odoo = _get_odoo()

        try:
            # Verificar la versión de Odoo para determinar el modelo correcto
            # En Odoo 13.0+, se usa 'stock.inventory'
            # En Odoo 15.0+, se usa 'stock.quant' directamente

            # Intentar obtener el modelo stock.inventory
            inventory_model_exists = odoo.execute_method(
                "ir.model",
                "search_count",
                [("model", "=", "stock.inventory")]
            ) > 0

            if inventory_model_exists:
                # Usar el flujo de stock.inventory (Odoo 13.0, 14.0)
                # Crear el inventario
                inventory_vals = {
                    "name": name,
                    "line_ids": []
                }

                if date:
                    try:
                        datetime.strptime(date, "%Y-%m-%d")
                        inventory_vals["date"] = date
                    except ValueError:
                        return {"success": False, "error": f"Formato de fecha inválido: {date}. Use YYYY-MM-DD."}

                # Crear el inventario
                inventory_id = odoo.execute_method("stock.inventory", "create", inventory_vals)

                # Añadir líneas al inventario
                for line in adjustment_lines:
                    if not isinstance(line, dict):
                        return {"success": False, "error": "Cada línea debe ser un diccionario"}

                    if "product_id" not in line or "location_id" not in line or "product_qty" not in line:
                        return {"success": False, "error": "Cada línea debe contener product_id, location_id y product_qty"}

                    line_vals = {
                        "inventory_id": inventory_id,
                        "product_id": line["product_id"],
                        "location_id": line["location_id"],
                        "product_qty": line["product_qty"]
                    }

                    odoo.execute_method("stock.inventory.line", "create", line_vals)
                
                # Confirmar el inventario
                odoo.execute_method("stock.inventory", "action_validate", [inventory_id])
                
                return {
                    "success": True,
                    "result": {
                        "inventory_id": inventory_id,
                        "name": name
                    }
                }
            else:
                # Usar el flujo de stock.quant (Odoo 15.0+)
                result_ids = []

                for line in adjustment_lines:
                    if not isinstance(line, dict):
                        return {"success": False, "error": "Cada línea debe ser un diccionario"}

                    if "product_id" not in line or "location_id" not in line or "product_qty" not in line:
                        return {"success": False, "error": "Cada línea debe contener product_id, location_id y product_qty"}
                    # Buscar el quant existente
                    quant_domain = [
                        ("product_id", "=", line["product_id"]),
                        ("location_id", "=", line["location_id"])
                    ]

                    quants = odoo.search_read(
                        "stock.quant",
                        quant_domain,
                        fields=["id", "quantity"]
                    )

                    if quants:
                        # Actualizar quant existente
                        quant_id = quants[0]["id"]
                        odoo.execute_method(
                            "stock.quant",
                            "write",
                            [quant_id],
                            {"inventory_quantity": line["product_qty"]}
                        )
                        result_ids.append(quant_id)
                    else:
                        # Crear nuevo quant
                        quant_vals = {
                            "product_id": line["product_id"],
                            "location_id": line["location_id"],
                            "inventory_quantity": line["product_qty"]
                        }
                        quant_id = odoo.execute_method("stock.quant", "create", quant_vals)
                        result_ids.append(quant_id)
                
                # Aplicar el inventario
                odoo.execute_method("stock.quant", "action_apply_inventory", result_ids)
                
                return {
                    "success": True,
                    "result": {
                        "quant_ids": result_ids,
                        "name": name
                    }
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Calcula y analiza la rotación de inventario")
    def analyze_inventory_turnover(
        date_from: str,
        date_to: str,
        product_ids: Optional[List[int]] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calcula y analiza la rotación de inventario

        Args:
            date_from: Fecha inicial en formato YYYY-MM-DD
            date_to: Fecha final en formato YYYY-MM-DD
            product_ids: Lista de IDs de productos a analizar (opcional)
            category_id: ID de categoría de producto para filtrar (opcional)

        Returns:
            Diccionario con resultados del análisis
        """
        odoo = _get_odoo()

        try:
            # Validar fechas
            try:
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Formato de fecha inválido. Use YYYY-MM-DD."}

            # Construir dominio para productos
            product_domain = [("type", "=", "product")]  # Solo productos almacenables

            if product_ids:
                product_domain.append(("id", "in", product_ids))

            if category_id:
                product_domain.append(("categ_id", "=", category_id))
            
            # Obtener productos
            products = odoo.search_read(
                "product.product",
                product_domain,
                fields=["name", "default_code", "categ_id", "standard_price"]
            )
            
            if not products:
                return {"success": False, "error": "No se encontraron productos con los criterios especificados"}
            
            # Calcular rotación para cada producto
            product_turnover = {}
            
            for product in products:
                product_id = product["id"]
                
                # 1. Obtener movimientos de salida (ventas) en el período
                outgoing_domain = [
                    ("product_id", "=", product_id),
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("location_dest_id.usage", "=", "customer")  # Destino: cliente
                ]
                
                outgoing_moves = odoo.search_read(
                    "stock.move",
                    outgoing_domain,
                    fields=["product_uom_qty", "price_unit"]
                )
                
                # Calcular costo de ventas
                cogs = sum(move["product_uom_qty"] * (move.get("price_unit") or product["standard_price"]) for move in outgoing_moves)
                
                # 2. Obtener valor de inventario promedio
                # Intentar obtener valoración de inventario al inicio y fin del período
                
                # Método 1: Usar informes de valoración si están disponibles
                try:
                    # Valoración al inicio del período
                    context_start = {
                        "to_date": date_from
                    }
                    
                    valuation_start = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["stock_value"],
                        context_start
                    )
                    
                    # Valoración al final del período
                    context_end = {
                        "to_date": date_to
                    }
                    
                    valuation_end = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["stock_value"],
                        context_end
                    )
                    
                    start_value = valuation_start[0]["stock_value"] if valuation_start else 0
                    end_value = valuation_end[0]["stock_value"] if valuation_end else 0
                    
                    avg_inventory_value = (start_value + end_value) / 2
                    
                except Exception:
                    # Método 2: Estimación basada en precio estándar y cantidad
                    # Obtener cantidad al inicio
                    context_start = {
                        "to_date": date_from
                    }
                    
                    qty_start = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["qty_available"],
                        context_start
                    )
                    
                    # Obtener cantidad al final
                    context_end = {
                        "to_date": date_to
                    }
                    
                    qty_end = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["qty_available"],
                        context_end
                    )
                    
                    start_qty = qty_start[0]["qty_available"] if qty_start else 0
                    end_qty = qty_end[0]["qty_available"] if qty_end else 0
                    
                    avg_qty = (start_qty + end_qty) / 2
                    avg_inventory_value = avg_qty * product["standard_price"]
                
                # 3. Calcular métricas de rotación
                turnover_ratio = 0
                days_inventory = 0
                
                if avg_inventory_value > 0:
                    turnover_ratio = cogs / avg_inventory_value

                    # Días de inventario (basado en el período analizado)
                    days_in_period = (date_to_dt - date_from_dt).days + 1
                    if turnover_ratio > 0:
                        days_inventory = days_in_period / turnover_ratio
                
                # Guardar resultados
                product_turnover[product_id] = {
                    "name": product["name"],
                    "default_code": product["default_code"],
                    "category": product["categ_id"][1] if product["categ_id"] else "Sin categoría",
                    "cogs": cogs,
                    "avg_inventory_value": avg_inventory_value,
                    "turnover_ratio": turnover_ratio,
                    "days_inventory": days_inventory
                }
            
            # Ordenar productos por rotación (de mayor a menor)
            sorted_products = sorted(
                product_turnover.items(),
                key=lambda x: x[1]["turnover_ratio"],
                reverse=True
            )
            
            # Calcular promedios generales
            total_cogs = sum(data["cogs"] for _, data in product_turnover.items())
            total_avg_value = sum(data["avg_inventory_value"] for _, data in product_turnover.items())
            
            overall_turnover = 0
            overall_days = 0
            
            if total_avg_value > 0:
                overall_turnover = total_cogs / total_avg_value
                days_in_period = (date_to_dt - date_from_dt).days + 1
                if overall_turnover > 0:
                    overall_days = days_in_period / overall_turnover
            
            # Preparar resultado
            result = {
                "period": {
                    "from": date_from,
                    "to": date_to,
                    "days": (date_to_dt - date_from_dt).days + 1
                },
                "summary": {
                    "product_count": len(products),
                    "total_cogs": total_cogs,
                    "total_avg_inventory_value": total_avg_value,
                    "overall_turnover_ratio": overall_turnover,
                    "overall_days_inventory": overall_days
                },
                "products": [
                    {"id": k, **v} for k, v in sorted_products
                ]
            }
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
