"""
Implementación de herramientas (tools) para ventas en MCP-Odoo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastmcp import FastMCP

from .models import (
    SalesOrderFilter,
    SalesOrderCreate,
    SalesPerformanceInput
)
from .odoo_client import get_odoo_client

def register_sales_tools(mcp: FastMCP) -> None:
    """Registra herramientas relacionadas con ventas"""

    # Helper function to get Odoo client
    def _get_odoo():
        return get_odoo_client()

    @mcp.tool(description="Busca pedidos de venta con filtros avanzados")
    def search_sales_orders(
        partner_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        order: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca pedidos de venta según los filtros especificados

        Args:
            partner_id: Filtrar por cliente ID (opcional)
            date_from: Fecha inicial en formato YYYY-MM-DD (opcional)
            date_to: Fecha final en formato YYYY-MM-DD (opcional)
            state: Estado del pedido, ej: 'sale', 'draft', 'done' (opcional)
            limit: Límite de resultados (default: 20)
            offset: Offset para paginación (default: 0)
            order: Criterio de ordenación, ej: 'date_order DESC' (opcional)

        Returns:
            Diccionario con resultados de la búsqueda
        """
        odoo = _get_odoo()

        try:
            # Construir dominio de búsqueda
            domain = []

            if partner_id:
                domain.append(("partner_id", "=", partner_id))

            if date_from:
                try:
                    datetime.strptime(date_from, "%Y-%m-%d")
                    domain.append(("date_order", ">=", date_from))
                except ValueError:
                    return {"success": False, "error": f"Formato de fecha inválido: {date_from}. Use YYYY-MM-DD."}

            if date_to:
                try:
                    datetime.strptime(date_to, "%Y-%m-%d")
                    domain.append(("date_order", "<=", date_to))
                except ValueError:
                    return {"success": False, "error": f"Formato de fecha inválido: {date_to}. Use YYYY-MM-DD."}

            if state:
                domain.append(("state", "=", state))

            # Campos a recuperar
            fields = [
                "name", "partner_id", "date_order", "amount_total",
                "state", "invoice_status", "user_id", "order_line"
            ]

            # Ejecutar búsqueda
            orders = odoo.search_read(
                "sale.order",
                domain,
                fields=fields,
                limit=limit,
                offset=offset,
                order=order
            )

            # Obtener el conteo total sin límite para paginación
            total_count = odoo.execute_method("sale.order", "search_count", domain)

            return {
                "success": True,
                "result": {
                    "count": len(orders),
                    "total_count": total_count,
                    "orders": orders
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Crear un nuevo pedido de venta")
    def create_sales_order(
        partner_id: int,
        order_lines: List[Dict[str, Any]],
        date_order: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo pedido de venta

        Args:
            partner_id: ID del cliente
            order_lines: Lista de líneas del pedido. Cada línea debe tener:
                - product_id (int): ID del producto
                - product_uom_qty (float): Cantidad
                - price_unit (float, opcional): Precio unitario
            date_order: Fecha del pedido en formato YYYY-MM-DD (opcional)

        Returns:
            Respuesta con el resultado de la operación
        """
        odoo = _get_odoo()

        try:
            # Preparar valores para el pedido
            order_vals = {
                "partner_id": partner_id,
                "order_line": []
            }

            if date_order:
                try:
                    datetime.strptime(date_order, "%Y-%m-%d")
                    order_vals["date_order"] = date_order
                except ValueError:
                    return {"success": False, "error": f"Formato de fecha inválido: {date_order}. Use YYYY-MM-DD."}

            # Preparar líneas de pedido
            for line in order_lines:
                if not isinstance(line, dict):
                    return {"success": False, "error": "Cada línea debe ser un diccionario"}

                if "product_id" not in line or "product_uom_qty" not in line:
                    return {"success": False, "error": "Cada línea debe contener product_id y product_uom_qty"}

                line_vals = [
                    0, 0, {
                        "product_id": line["product_id"],
                        "product_uom_qty": line["product_uom_qty"]
                    }
                ]

                if "price_unit" in line and line["price_unit"] is not None:
                    line_vals[2]["price_unit"] = line["price_unit"]

                order_vals["order_line"].append(line_vals)

            # Crear pedido
            order_id = odoo.execute_method("sale.order", "create", order_vals)

            # Obtener información del pedido creado
            order_info = odoo.execute_method("sale.order", "read", [order_id], ["name"])[0]

            return {
                "success": True,
                "result": {
                    "order_id": order_id,
                    "order_name": order_info["name"]
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Analiza el rendimiento de ventas en un período")
    def analyze_sales_performance(
        date_from: str,
        date_to: str,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza el rendimiento de ventas en un período específico

        Args:
            date_from: Fecha inicial en formato YYYY-MM-DD
            date_to: Fecha final en formato YYYY-MM-DD
            group_by: Agrupar resultados por 'product', 'customer', o 'salesperson' (opcional)

        Returns:
            Diccionario con resultados del análisis
        """
        odoo = _get_odoo()

        try:
            # Validar fechas
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
                datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Formato de fecha inválido. Use YYYY-MM-DD."}

            # Construir dominio para pedidos confirmados
            domain = [
                ("date_order", ">=", date_from),
                ("date_order", "<=", date_to),
                ("state", "in", ["sale", "done"])
            ]
            
            # Obtener datos de ventas
            sales_data = odoo.search_read(
                "sale.order",
                domain,
                fields=["name", "partner_id", "date_order", "amount_total", "user_id"]
            )

            # Calcular período anterior para comparación
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
            delta = date_to_dt - date_from_dt

            prev_date_to = date_from_dt - timedelta(days=1)
            prev_date_from = prev_date_to - delta
            
            prev_domain = [
                ("date_order", ">=", prev_date_from.strftime("%Y-%m-%d")),
                ("date_order", "<=", prev_date_to.strftime("%Y-%m-%d")),
                ("state", "in", ["sale", "done"])
            ]
            
            prev_sales_data = odoo.search_read(
                "sale.order",
                prev_domain,
                fields=["amount_total"]
            )
            
            # Calcular totales
            current_total = sum(order["amount_total"] for order in sales_data)
            previous_total = sum(order["amount_total"] for order in prev_sales_data)
            
            # Calcular cambio porcentual
            percent_change = 0
            if previous_total > 0:
                percent_change = ((current_total - previous_total) / previous_total) * 100
            
            # Agrupar según el parámetro group_by
            grouped_data = {}
            if group_by:
                if group_by == "product":
                    # Obtener líneas de pedido para analizar productos
                    order_ids = [order["id"] for order in sales_data]
                    if order_ids:
                        order_lines = odoo.search_read(
                            "sale.order.line",
                            [("order_id", "in", order_ids)],
                            fields=["product_id", "product_uom_qty", "price_subtotal"]
                        )
                        
                        # Agrupar por producto
                        product_data = {}
                        for line in order_lines:
                            product_id = line["product_id"][0] if line["product_id"] else 0
                            product_name = line["product_id"][1] if line["product_id"] else "Desconocido"
                            
                            if product_id not in product_data:
                                product_data[product_id] = {
                                    "name": product_name,
                                    "quantity": 0,
                                    "amount": 0
                                }
                            
                            product_data[product_id]["quantity"] += line["product_uom_qty"]
                            product_data[product_id]["amount"] += line["price_subtotal"]
                        
                        # Ordenar por monto
                        top_products = sorted(
                            product_data.items(),
                            key=lambda x: x[1]["amount"],
                            reverse=True
                        )
                        
                        grouped_data["products"] = [
                            {"id": k, **v} for k, v in top_products[:10]
                        ]
                
                elif group_by == "customer":
                    # Agrupar por cliente
                    customer_data = {}
                    for order in sales_data:
                        customer_id = order["partner_id"][0] if order["partner_id"] else 0
                        customer_name = order["partner_id"][1] if order["partner_id"] else "Desconocido"
                        
                        if customer_id not in customer_data:
                            customer_data[customer_id] = {
                                "name": customer_name,
                                "order_count": 0,
                                "amount": 0
                            }
                        
                        customer_data[customer_id]["order_count"] += 1
                        customer_data[customer_id]["amount"] += order["amount_total"]
                    
                    # Ordenar por monto
                    top_customers = sorted(
                        customer_data.items(),
                        key=lambda x: x[1]["amount"],
                        reverse=True
                    )
                    
                    grouped_data["customers"] = [
                        {"id": k, **v} for k, v in top_customers[:10]
                    ]
                
                elif group_by == "salesperson":
                    # Agrupar por vendedor
                    salesperson_data = {}
                    for order in sales_data:
                        salesperson_id = order["user_id"][0] if order["user_id"] else 0
                        salesperson_name = order["user_id"][1] if order["user_id"] else "Desconocido"
                        
                        if salesperson_id not in salesperson_data:
                            salesperson_data[salesperson_id] = {
                                "name": salesperson_name,
                                "order_count": 0,
                                "amount": 0
                            }
                        
                        salesperson_data[salesperson_id]["order_count"] += 1
                        salesperson_data[salesperson_id]["amount"] += order["amount_total"]
                    
                    # Ordenar por monto
                    top_salespersons = sorted(
                        salesperson_data.items(),
                        key=lambda x: x[1]["amount"],
                        reverse=True
                    )
                    
                    grouped_data["salespersons"] = [
                        {"id": k, **v} for k, v in top_salespersons
                    ]
            
            # Preparar resultado
            result = {
                "period": {
                    "from": date_from,
                    "to": date_to
                },
                "summary": {
                    "order_count": len(sales_data),
                    "total_amount": current_total,
                    "previous_period": {
                        "from": prev_date_from.strftime("%Y-%m-%d"),
                        "to": prev_date_to.strftime("%Y-%m-%d"),
                        "order_count": len(prev_sales_data),
                        "total_amount": previous_total
                    },
                    "percent_change": round(percent_change, 2)
                }
            }
            
            # Añadir datos agrupados si existen
            if grouped_data:
                result["grouped_data"] = grouped_data
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
