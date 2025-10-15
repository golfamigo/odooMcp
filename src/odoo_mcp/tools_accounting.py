"""
Implementación de herramientas (tools) para contabilidad en MCP-Odoo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastmcp import FastMCP

from .models import (
    JournalEntryFilter,
    JournalEntryCreate,
    FinancialRatioInput
)
from .odoo_client import get_odoo_client

def register_accounting_tools(mcp: FastMCP) -> None:
    """Registra herramientas relacionadas con contabilidad"""

    # Helper function to get Odoo client
    def _get_odoo():
        return get_odoo_client()

    @mcp.tool(description="Busca asientos contables con filtros")
    def search_journal_entries(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        journal_id: Optional[int] = None,
        state: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Busca asientos contables según los filtros especificados

        Args:
            date_from: Fecha inicial en formato YYYY-MM-DD (opcional)
            date_to: Fecha final en formato YYYY-MM-DD (opcional)
            journal_id: Filtrar por diario contable ID (opcional)
            state: Estado del asiento, ej: 'posted', 'draft' (opcional)
            limit: Límite de resultados (default: 20)
            offset: Offset para paginación (default: 0)

        Returns:
            Diccionario con resultados de la búsqueda
        """
        odoo = _get_odoo()

        try:
            # Construir dominio de búsqueda
            domain = []

            if date_from:
                try:
                    datetime.strptime(date_from, "%Y-%m-%d")
                    domain.append(("date", ">=", date_from))
                except ValueError:
                    return {"success": False, "error": f"Formato de fecha inválido: {date_from}. Use YYYY-MM-DD."}

            if date_to:
                try:
                    datetime.strptime(date_to, "%Y-%m-%d")
                    domain.append(("date", "<=", date_to))
                except ValueError:
                    return {"success": False, "error": f"Formato de fecha inválido: {date_to}. Use YYYY-MM-DD."}

            if journal_id:
                domain.append(("journal_id", "=", journal_id))

            if state:
                domain.append(("state", "=", state))

            # Campos a recuperar
            fields = [
                "name", "ref", "date", "journal_id", "state",
                "amount_total", "amount_total_signed", "line_ids"
            ]

            # Ejecutar búsqueda
            entries = odoo.search_read(
                "account.move",
                domain,
                fields=fields,
                limit=limit,
                offset=offset
            )
            
            # Obtener el conteo total sin límite para paginación
            total_count = odoo.execute_method("account.move", "search_count", domain)
            
            # Para cada asiento, obtener información resumida de las líneas
            for entry in entries:
                if entry.get("line_ids"):
                    line_ids = entry["line_ids"]
                    lines = odoo.search_read(
                        "account.move.line",
                        [("id", "in", line_ids)],
                        fields=["name", "account_id", "partner_id", "debit", "credit", "balance"]
                    )
                    entry["lines"] = lines
                    # Eliminar la lista de IDs para reducir tamaño
                    entry.pop("line_ids", None)
            
            return {
                "success": True, 
                "result": {
                    "count": len(entries),
                    "total_count": total_count,
                    "entries": entries
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Crea un nuevo asiento contable")
    def create_journal_entry(
        journal_id: int,
        lines: List[Dict[str, Any]],
        ref: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo asiento contable

        Args:
            journal_id: ID del diario contable
            lines: Lista de líneas del asiento. Cada línea debe tener:
                - account_id (int): ID de la cuenta contable
                - debit (float): Importe al debe (default: 0.0)
                - credit (float): Importe al haber (default: 0.0)
                - name (str, opcional): Descripción de la línea
                - partner_id (int, opcional): ID del partner
            ref: Referencia del asiento (opcional)
            date: Fecha del asiento en formato YYYY-MM-DD (opcional)

        Returns:
            Respuesta con el resultado de la operación
        """
        odoo = _get_odoo()

        try:
            # Validar líneas
            if not lines:
                return {"success": False, "error": "Debe proporcionar al menos una línea"}

            # Verificar que el debe y el haber cuadran
            total_debit = sum(line.get("debit", 0.0) for line in lines)
            total_credit = sum(line.get("credit", 0.0) for line in lines)

            if round(total_debit, 2) != round(total_credit, 2):
                return {
                    "success": False,
                    "error": f"El asiento no está cuadrado. Debe: {total_debit}, Haber: {total_credit}"
                }

            # Preparar valores para el asiento
            move_vals = {
                "journal_id": journal_id,
                "line_ids": []
            }

            if ref:
                move_vals["ref"] = ref

            if date:
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                    move_vals["date"] = date
                except ValueError:
                    return {"success": False, "error": f"Formato de fecha inválido: {date}. Use YYYY-MM-DD."}

            # Preparar líneas del asiento
            for line in lines:
                if not isinstance(line, dict):
                    return {"success": False, "error": "Cada línea debe ser un diccionario"}

                if "account_id" not in line:
                    return {"success": False, "error": "Cada línea debe contener account_id"}

                line_vals = [
                    0, 0, {
                        "account_id": line["account_id"],
                        "name": line.get("name") or "/",
                        "debit": line.get("debit", 0.0),
                        "credit": line.get("credit", 0.0)
                    }
                ]

                if "partner_id" in line and line["partner_id"]:
                    line_vals[2]["partner_id"] = line["partner_id"]

                move_vals["line_ids"].append(line_vals)
            
            # Crear asiento
            move_id = odoo.execute_method("account.move", "create", move_vals)
            
            # Obtener información del asiento creado
            move_info = odoo.execute_method("account.move", "read", [move_id], ["name", "state"])[0]
            
            return {
                "success": True,
                "result": {
                    "move_id": move_id,
                    "name": move_info["name"],
                    "state": move_info["state"]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Calcula ratios financieros clave")
    def analyze_financial_ratios(
        date_from: str,
        date_to: str,
        ratios: List[str]
    ) -> Dict[str, Any]:
        """
        Calcula ratios financieros clave para un período específico

        Args:
            date_from: Fecha inicial en formato YYYY-MM-DD
            date_to: Fecha final en formato YYYY-MM-DD
            ratios: Lista de ratios a calcular. Opciones:
                - 'liquidity': Ratios de liquidez
                - 'profitability': Ratios de rentabilidad
                - 'debt': Ratios de endeudamiento
                - 'efficiency': Ratios de eficiencia

        Returns:
            Diccionario con los ratios calculados
        """
        odoo = _get_odoo()

        try:
            # Validar fechas
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
                datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Formato de fecha inválido. Use YYYY-MM-DD."}

            # Verificar qué ratios se solicitan
            requested_ratios = ratios

            # Inicializar resultado
            ratios_result = {}

            # Obtener datos del balance general
            # Activos
            assets_domain = [
                ("account_id.user_type_id.internal_group", "=", "asset"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            assets_data = odoo.search_read(
                "account.move.line",
                assets_domain,
                fields=["account_id", "balance"]
            )
            
            total_assets = sum(line["balance"] for line in assets_data)
            
            # Activos corrientes
            current_assets_domain = [
                ("account_id.user_type_id.internal_group", "=", "asset"),
                ("account_id.user_type_id.type", "=", "liquidity"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            current_assets_data = odoo.search_read(
                "account.move.line",
                current_assets_domain,
                fields=["account_id", "balance"]
            )
            
            current_assets = sum(line["balance"] for line in current_assets_data)
            
            # Pasivos
            liabilities_domain = [
                ("account_id.user_type_id.internal_group", "=", "liability"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            liabilities_data = odoo.search_read(
                "account.move.line",
                liabilities_domain,
                fields=["account_id", "balance"]
            )
            
            total_liabilities = sum(line["balance"] for line in liabilities_data)
            
            # Pasivos corrientes
            current_liabilities_domain = [
                ("account_id.user_type_id.internal_group", "=", "liability"),
                ("account_id.user_type_id.type", "=", "payable"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            current_liabilities_data = odoo.search_read(
                "account.move.line",
                current_liabilities_domain,
                fields=["account_id", "balance"]
            )
            
            current_liabilities = sum(line["balance"] for line in current_liabilities_data)
            
            # Patrimonio
            equity_domain = [
                ("account_id.user_type_id.internal_group", "=", "equity"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            equity_data = odoo.search_read(
                "account.move.line",
                equity_domain,
                fields=["account_id", "balance"]
            )
            
            total_equity = sum(line["balance"] for line in equity_data)
            
            # Ingresos
            income_domain = [
                ("account_id.user_type_id.internal_group", "=", "income"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            income_data = odoo.search_read(
                "account.move.line",
                income_domain,
                fields=["account_id", "balance"]
            )
            
            total_income = sum(line["balance"] for line in income_data)
            
            # Gastos
            expense_domain = [
                ("account_id.user_type_id.internal_group", "=", "expense"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("parent_state", "=", "posted")
            ]
            
            expense_data = odoo.search_read(
                "account.move.line",
                expense_domain,
                fields=["account_id", "balance"]
            )
            
            total_expenses = sum(line["balance"] for line in expense_data)
            
            # Calcular beneficio neto
            net_income = total_income - total_expenses
            
            # Calcular ratios solicitados
            if "liquidity" in requested_ratios:
                # Ratio de liquidez corriente
                current_ratio = 0
                if current_liabilities != 0:
                    current_ratio = current_assets / abs(current_liabilities)

                ratios_result["liquidity"] = {
                    "current_ratio": current_ratio,
                    "current_assets": current_assets,
                    "current_liabilities": abs(current_liabilities)
                }
            
            if "profitability" in requested_ratios:
                # Rentabilidad sobre activos (ROA)
                roa = 0
                if total_assets != 0:
                    roa = (net_income / total_assets) * 100
                
                # Rentabilidad sobre patrimonio (ROE)
                roe = 0
                if total_equity != 0:
                    roe = (net_income / total_equity) * 100
                
                # Margen de beneficio neto
                profit_margin = 0
                if total_income != 0:
                    profit_margin = (net_income / total_income) * 100

                ratios_result["profitability"] = {
                    "return_on_assets": roa,
                    "return_on_equity": roe,
                    "net_profit_margin": profit_margin,
                    "net_income": net_income,
                    "total_income": total_income
                }
            
            if "debt" in requested_ratios:
                # Ratio de endeudamiento
                debt_ratio = 0
                if total_assets != 0:
                    debt_ratio = (abs(total_liabilities) / total_assets) * 100
                
                # Ratio de apalancamiento
                leverage_ratio = 0
                if total_equity != 0:
                    leverage_ratio = (abs(total_liabilities) / total_equity)

                ratios_result["debt"] = {
                    "debt_ratio": debt_ratio,
                    "leverage_ratio": leverage_ratio,
                    "total_liabilities": abs(total_liabilities),
                    "total_equity": total_equity
                }
            
            if "efficiency" in requested_ratios:
                # Rotación de activos
                asset_turnover = 0
                if total_assets != 0:
                    asset_turnover = total_income / total_assets

                ratios_result["efficiency"] = {
                    "asset_turnover": asset_turnover
                }
            
            # Preparar resultado
            result = {
                "period": {
                    "from": date_from,
                    "to": date_to
                },
                "summary": {
                    "total_assets": total_assets,
                    "total_liabilities": abs(total_liabilities),
                    "total_equity": total_equity,
                    "total_income": total_income,
                    "total_expenses": abs(total_expenses),
                    "net_income": net_income
                },
                "ratios": ratios_result
            }
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
