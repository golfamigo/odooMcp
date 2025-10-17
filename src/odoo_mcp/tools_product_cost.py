"""
產品成本分析工具 - 專注於進口貿易的成本結構
"""

from typing import Dict, List, Any, Optional
from fastmcp import FastMCP
from .odoo_client import get_odoo_client


def register_product_cost_tools(mcp: FastMCP) -> None:
    """註冊產品成本分析相關工具"""

    def _get_odoo():
        return get_odoo_client()

    @mcp.tool(description="分析產品的成本結構、毛利率，並支援排序和篩選")
    def analyze_product_costs(
        limit: int = 20,
        category_id: Optional[int] = None,
        min_profit_margin: Optional[float] = None,
        sort_by: str = "profit_margin",  # profit_margin, profit_amount, sales_price
        currency: str = "PHP"
    ) -> Dict[str, Any]:
        """
        分析產品的完整成本結構和毛利

        Parameters:
            limit: 返回產品數量（預設 20，最大 100）
            category_id: 產品分類 ID（可選）
            min_profit_margin: 最低毛利率過濾（例如 0.2 = 20%）
            sort_by: 排序依據
                - "profit_margin": 按毛利率排序（預設）
                - "profit_amount": 按毛利金額排序
                - "sales_price": 按售價排序
                - "cost": 按成本排序
            currency: 幣別（預設 PHP）

        Returns:
            包含產品成本分析的字典：
            - products: 產品列表，每個包含：
                - id, name, default_code（料號）
                - list_price（售價）
                - standard_price（落地成本）
                - profit_amount（毛利金額）
                - profit_margin（毛利率 %）
                - base_cost_rmb（基礎成本 RMB）
                - exchange_rate（匯率）
                - service_fee, shipping_fee, ocean_fee, si_fee
            - summary: 統計摘要
                - total_products: 產品總數
                - avg_profit_margin: 平均毛利率
                - highest_margin: 最高毛利率
                - lowest_margin: 最低毛利率

        Examples:
            # 查詢毛利率最高的 5 個產品
            analyze_product_costs(limit=5, sort_by="profit_margin")

            # 查詢毛利金額最高的 10 個產品
            analyze_product_costs(limit=10, sort_by="profit_amount")

            # 查詢毛利率 > 30% 的產品
            analyze_product_costs(limit=50, min_profit_margin=0.3)
        """
        odoo = _get_odoo()

        try:
            # 限制最大查詢數量
            if limit > 100:
                limit = 100

            # 構建查詢條件
            domain = [("sale_ok", "=", True)]
            if category_id:
                domain.append(("categ_id", "=", category_id))

            # 查詢產品，只要必要欄位
            products = odoo.execute_method(
                "product.template",
                "search_read",
                domain=domain,
                fields=[
                    "id", "name", "default_code",
                    "list_price", "standard_price",
                    "categ_id", "currency_id",
                    # 自訂成本欄位
                    "x_base_cost_rmb",
                    "x_exchange_rate",
                    "x_service_fee_rate",
                    "x_shipping_fee",
                    "x_ocean_fee",
                    "x_si_fee_rate",
                    "x_landed_cost",
                    "x_margin",
                    "x_margin_percent"
                ],
                limit=min(limit, 50)  # 限制最大 50，避免 timeout
            )

            if not products:
                return {
                    "success": False,
                    "error": "未找到符合條件的產品"
                }

            # 計算成本分析
            analyzed_products = []
            for p in products:
                list_price = p.get("list_price", 0)
                standard_price = p.get("standard_price", 0)

                # 計算毛利
                profit_amount = list_price - standard_price
                profit_margin = (profit_amount / list_price * 100) if list_price > 0 else 0

                # 過濾毛利率
                if min_profit_margin and (profit_margin / 100) < min_profit_margin:
                    continue

                analyzed_products.append({
                    "id": p.get("id"),
                    "name": p.get("name", "N/A"),
                    "default_code": p.get("default_code", "N/A"),
                    "category": p.get("categ_id", [False, "N/A"])[1] if p.get("categ_id") else "N/A",
                    "sales_price": list_price,
                    "landed_cost": standard_price,
                    "profit_amount": profit_amount,
                    "profit_margin": round(profit_margin, 2),
                    "currency": p.get("currency_id", [False, currency])[1] if p.get("currency_id") else currency,
                    # 成本明細
                    "cost_breakdown": {
                        "base_cost_rmb": p.get("x_base_cost_rmb", 0),
                        "exchange_rate": p.get("x_exchange_rate", 0),
                        "service_fee_rate": p.get("x_service_fee_rate", 0),
                        "shipping_fee": p.get("x_shipping_fee", 0),
                        "ocean_fee": p.get("x_ocean_fee", 0),
                        "si_fee_rate": p.get("x_si_fee_rate", 0)
                    }
                })

            # 排序
            sort_keys = {
                "profit_margin": lambda x: x["profit_margin"],
                "profit_amount": lambda x: x["profit_amount"],
                "sales_price": lambda x: x["sales_price"],
                "cost": lambda x: x["landed_cost"]
            }

            if sort_by in sort_keys:
                analyzed_products.sort(key=sort_keys[sort_by], reverse=True)

            # 取前 limit 筆
            analyzed_products = analyzed_products[:limit]

            # 計算統計摘要
            if analyzed_products:
                margins = [p["profit_margin"] for p in analyzed_products]
                summary = {
                    "total_products": len(analyzed_products),
                    "avg_profit_margin": round(sum(margins) / len(margins), 2),
                    "highest_margin": max(margins),
                    "lowest_margin": min(margins),
                    "total_profit": sum(p["profit_amount"] for p in analyzed_products)
                }
            else:
                summary = {
                    "total_products": 0,
                    "avg_profit_margin": 0,
                    "highest_margin": 0,
                    "lowest_margin": 0,
                    "total_profit": 0
                }

            return {
                "success": True,
                "products": analyzed_products,
                "summary": summary
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"查詢失敗: {str(e)}"
            }


    @mcp.tool(description="查詢單一產品的詳細成本結構")
    def get_product_cost_detail(
        product_id: Optional[int] = None,
        product_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查詢單一產品的詳細成本結構

        Parameters:
            product_id: 產品 ID（二選一）
            product_code: 產品料號 default_code（二選一）

        Returns:
            產品的完整成本明細

        Examples:
            # 用 ID 查詢
            get_product_cost_detail(product_id=132)

            # 用料號查詢
            get_product_cost_detail(product_code="GT-001S - ACC")
        """
        odoo = _get_odoo()

        try:
            # 構建查詢條件
            if product_id:
                domain = [("id", "=", product_id)]
            elif product_code:
                domain = [("default_code", "=", product_code)]
            else:
                return {
                    "success": False,
                    "error": "必須提供 product_id 或 product_code"
                }

            # 查詢產品
            products = odoo.execute_method(
                "product.template",
                "search_read",
                domain=domain,
                fields=[
                    "id", "name", "default_code",
                    "list_price", "standard_price",
                    "categ_id", "currency_id",
                    "x_base_cost_rmb",
                    "x_exchange_rate",
                    "x_service_fee_rate",
                    "x_shipping_fee",
                    "x_ocean_fee",
                    "x_si_fee_rate",
                    "x_landed_cost",
                    "x_margin",
                    "x_margin_percent",
                    "x_cost_calculated_date"
                ],
                limit=1
            )

            if not products:
                return {
                    "success": False,
                    "error": "未找到該產品"
                }

            p = products[0]
            list_price = p.get("list_price", 0)
            standard_price = p.get("standard_price", 0)
            base_cost_rmb = p.get("x_base_cost_rmb", 0)
            exchange_rate = p.get("x_exchange_rate", 0)

            # 計算各項成本（PHP）
            base_cost_php = base_cost_rmb * exchange_rate if exchange_rate else 0
            service_fee = base_cost_php * p.get("x_service_fee_rate", 0) if base_cost_php else 0
            shipping_fee = p.get("x_shipping_fee", 0)
            ocean_fee = p.get("x_ocean_fee", 0)
            si_fee = (base_cost_php + service_fee + shipping_fee + ocean_fee) * p.get("x_si_fee_rate", 0)

            profit_amount = list_price - standard_price
            profit_margin = (profit_amount / list_price * 100) if list_price > 0 else 0

            return {
                "success": True,
                "product": {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "default_code": p.get("default_code"),
                    "category": p.get("categ_id", [False, "N/A"])[1] if p.get("categ_id") else "N/A",
                    "currency": p.get("currency_id", [False, "PHP"])[1] if p.get("currency_id") else "PHP"
                },
                "pricing": {
                    "sales_price": list_price,
                    "landed_cost": standard_price,
                    "profit_amount": profit_amount,
                    "profit_margin_percent": round(profit_margin, 2)
                },
                "cost_breakdown": {
                    "base_cost_rmb": base_cost_rmb,
                    "exchange_rate": exchange_rate,
                    "base_cost_php": round(base_cost_php, 2),
                    "service_fee": round(service_fee, 2),
                    "service_fee_rate_percent": p.get("x_service_fee_rate", 0) * 100,
                    "shipping_fee": shipping_fee,
                    "ocean_fee": ocean_fee,
                    "si_fee": round(si_fee, 2),
                    "si_fee_rate_percent": p.get("x_si_fee_rate", 0) * 100,
                    "total_landed_cost": standard_price
                },
                "metadata": {
                    "cost_calculated_date": p.get("x_cost_calculated_date", "N/A")
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"查詢失敗: {str(e)}"
            }


    @mcp.tool(description="比較多個產品的成本和毛利")
    def compare_product_costs(
        product_codes: List[str]
    ) -> Dict[str, Any]:
        """
        比較多個產品的成本結構和毛利

        Parameters:
            product_codes: 產品料號列表（最多 10 個）

        Returns:
            產品比較表

        Example:
            compare_product_costs(product_codes=["GT-001S - ACC", "Q348L", "HP1000"])
        """
        odoo = _get_odoo()

        try:
            if len(product_codes) > 10:
                return {
                    "success": False,
                    "error": "最多只能比較 10 個產品"
                }

            products = odoo.execute_method(
                "product.template",
                "search_read",
                domain=[("default_code", "in", product_codes)],
                fields=[
                    "name", "default_code",
                    "list_price", "standard_price",
                    "x_base_cost_rmb", "x_exchange_rate",
                    "x_margin_percent"
                ],
                limit=10
            )

            if not products:
                return {
                    "success": False,
                    "error": "未找到任何產品"
                }

            comparison = []
            for p in products:
                comparison.append({
                    "code": p.get("default_code", "N/A"),
                    "name": p.get("name", "N/A"),
                    "sales_price": p.get("list_price", 0),
                    "cost": p.get("standard_price", 0),
                    "profit": p.get("list_price", 0) - p.get("standard_price", 0),
                    "margin_percent": round(p.get("x_margin_percent", 0), 2),
                    "base_cost_rmb": p.get("x_base_cost_rmb", 0),
                    "exchange_rate": p.get("x_exchange_rate", 0)
                })

            return {
                "success": True,
                "comparison": comparison,
                "total_compared": len(comparison)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"比較失敗: {str(e)}"
            }
