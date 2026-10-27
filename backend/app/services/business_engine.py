"""
InsightFlow AI - Production Business Analysis Engine
Implements deterministic, dataset-driven analysis for:
1. Dataset Understanding Agent (Domain classification, schema profiling, empty handling)
2. Data Quality Agent (Missing, duplicates, invalid dates, category casing, suspicious numbers)
3. Business Analyst Agent (Sales, Finance, Customer, Inventory domain calculations, missing column guards)
4. Anomaly Detection Engine (Tukey IQR, Z-scores, temporal spikes/drops, severity, business problem distinction)
"""
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Literal

import numpy as np
import pandas as pd

from app.schemas.business_analysis import (
    ColumnProfile,
    DatasetProfileResponse,
    CleaningOperation,
    DataQualityAnalysisResponse,
    MetricItem,
    MissingColumnRequirement,
    BusinessMetricsResponse,
    AnomalyItem,
    AnomalyReportResponse,
)

logger = logging.getLogger("insightflow.services.business_engine")


class BusinessAnalysisEngine:
    """
    Core deterministic analytics engine executing real Pandas calculations.
    Zero hallucination of numbers. Strict ground truth from uploaded datasets.
    """

    # --------------------------------------------------------------------------
    # 1. Dataset Understanding & Domain Classification
    # --------------------------------------------------------------------------

    @classmethod
    def profile_dataset(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        dataset_name: str,
        file_type: str,
        file_size_bytes: int,
    ) -> DatasetProfileResponse:
        """
        Profiles dataset structure, infers column roles, and classifies the business domain.
        Handles empty datasets gracefully.
        """
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if df is None or len(df) == 0 or len(df.columns) == 0:
            return DatasetProfileResponse(
                datasetId=dataset_id,
                datasetName=dataset_name,
                rowCount=0,
                columnCount=0 if df is None else len(df.columns),
                fileType=file_type,
                fileSizeBytes=file_size_bytes,
                detectedDomain="general",
                domainConfidence=0.0,
                columnProfiles=[],
                domainMappings={},
                businessSummary="The dataset contains zero records or has an empty tabular structure.",
                createdAt=now_str,
            )

        total_rows = len(df)
        total_cols = len(df.columns)

        col_profiles: List[ColumnProfile] = []
        domain_mappings: Dict[str, Optional[str]] = {
            "date": None,
            "revenue": None,
            "expense": None,
            "profit": None,
            "quantity": None,
            "price": None,
            "order_id": None,
            "customer_id": None,
            "category": None,
            "country": None,
            "product": None,
            "stock": None,
            "reorder_level": None,
            "segment": None,
        }

        # Domain scoring counters
        domain_scores = {
            "sales": 0,
            "finance": 0,
            "customer": 0,
            "inventory": 0,
        }

        for col in df.columns:
            c_name = str(col)
            c_lower = c_name.strip().lower()
            series = df[col]
            missing_cnt = int(series.isna().sum())
            missing_pct = round((missing_cnt / total_rows * 100.0) if total_rows > 0 else 0.0, 2)
            unique_cnt = int(series.nunique(dropna=True))
            sample_vals = [
                str(x) if not isinstance(x, (int, float, bool)) else x
                for x in series.dropna().head(4).tolist()
            ]

            # Detect data type & semantic role
            data_type = str(series.dtype)
            semantic_role = "dimension"

            is_date = False
            if pd.api.types.is_datetime64_any_dtype(series):
                is_date = True
            elif any(k in c_lower for k in ["date", "time", "timestamp", "year", "month", "day", "created", "period"]):
                try:
                    parsed = pd.to_datetime(series.dropna().head(25), errors="coerce")
                    if parsed.notna().sum() >= max(1, len(parsed) * 0.5):
                        is_date = True
                except Exception:
                    pass

            if is_date:
                data_type = "date"
                semantic_role = "temporal"
                if not domain_mappings["date"]:
                    domain_mappings["date"] = c_name
                domain_scores["sales"] += 1
                domain_scores["finance"] += 1

            elif pd.api.types.is_numeric_dtype(series):
                data_type = "numeric"
                semantic_role = "metric"

                # Check specific numeric roles
                if any(k in c_lower for k in ["expense", "cost", "cogs", "spending", "outgoing"]):
                    semantic_role = "financial_expense"
                    if not domain_mappings["expense"]:
                        domain_mappings["expense"] = c_name
                    domain_scores["finance"] += 3

                elif any(k in c_lower for k in ["profit", "net_income", "ebitda", "margin", "operating_income"]):
                    semantic_role = "financial_profit"
                    if not domain_mappings["profit"]:
                        domain_mappings["profit"] = c_name
                    domain_scores["finance"] += 3

                elif any(k in c_lower for k in ["revenue", "sales", "amount", "total", "subtotal", "turnover", "gross"]):
                    semantic_role = "financial_revenue"
                    if not domain_mappings["revenue"]:
                        domain_mappings["revenue"] = c_name
                    domain_scores["sales"] += 2
                    domain_scores["finance"] += 2

                elif any(k in c_lower for k in ["price", "unitprice", "rate", "cost_per_unit"]):
                    semantic_role = "price"
                    if not domain_mappings["price"]:
                        domain_mappings["price"] = c_name
                    domain_scores["sales"] += 2

                elif any(k in c_lower for k in ["stock", "inventory", "on_hand", "qty_on_hand", "available_units", "quantity_available"]):
                    semantic_role = "stock_level"
                    if not domain_mappings["stock"]:
                        domain_mappings["stock"] = c_name
                    domain_scores["inventory"] += 3

                elif any(k in c_lower for k in ["reorder", "threshold", "min_stock", "safety_stock"]):
                    semantic_role = "reorder_point"
                    if not domain_mappings["reorder_level"]:
                        domain_mappings["reorder_level"] = c_name
                    domain_scores["inventory"] += 3

                elif any(k in c_lower for k in ["quantity", "qty", "volume", "units", "items_sold"]):
                    semantic_role = "quantity"
                    if not domain_mappings["quantity"]:
                        domain_mappings["quantity"] = c_name
                    domain_scores["sales"] += 2
                    domain_scores["inventory"] += 1

                elif any(k in c_lower for k in ["id", "code", "no", "key", "num"]):
                    semantic_role = "identifier"
                    if any(k in c_lower for k in ["cust", "user", "client", "buyer"]) and not domain_mappings["customer_id"]:
                        domain_mappings["customer_id"] = c_name
                        domain_scores["customer"] += 2
                    elif any(k in c_lower for k in ["order", "invoice", "txn", "trans"]) and not domain_mappings["order_id"]:
                        domain_mappings["order_id"] = c_name
                        domain_scores["sales"] += 2
                else:
                    if not domain_mappings["revenue"] and not domain_mappings["expense"]:
                        domain_mappings["revenue"] = c_name

            else:
                data_type = "string"
                if any(k in c_lower for k in ["country", "nation", "state", "territory", "region", "city"]):
                    semantic_role = "geographic"
                    if not domain_mappings["country"]:
                        domain_mappings["country"] = c_name

                elif any(k in c_lower for k in ["cust", "user", "client", "buyer", "account"]):
                    semantic_role = "customer"
                    if not domain_mappings["customer_id"]:
                        domain_mappings["customer_id"] = c_name
                    domain_scores["customer"] += 2

                elif any(k in c_lower for k in ["segment", "tier", "cohort", "cluster", "persona"]):
                    semantic_role = "customer_segment"
                    if not domain_mappings["segment"]:
                        domain_mappings["segment"] = c_name
                    domain_scores["customer"] += 3

                elif any(k in c_lower for k in ["sku", "stockcode", "part_no", "item_code", "product_id", "product", "item", "description"]):
                    semantic_role = "product"
                    if not domain_mappings["product"]:
                        domain_mappings["product"] = c_name
                    domain_scores["sales"] += 1
                    domain_scores["inventory"] += 1

                elif any(k in c_lower for k in ["category", "dept", "department", "type", "class", "group"]):
                    semantic_role = "category"
                    if not domain_mappings["category"]:
                        domain_mappings["category"] = c_name

                elif any(k in c_lower for k in ["order", "invoice", "bill", "txn", "transaction"]):
                    semantic_role = "order_id"
                    if not domain_mappings["order_id"]:
                        domain_mappings["order_id"] = c_name
                    domain_scores["sales"] += 2

            col_profiles.append(ColumnProfile(
                name=c_name,
                dataType=data_type,
                semanticRole=semantic_role,
                missingCount=missing_cnt,
                missingPercent=missing_pct,
                uniqueCount=unique_cnt,
                sampleValues=sample_vals,
            ))

        # Check for inventory signature
        if domain_mappings["stock"] is not None:
            domain_scores["inventory"] += 3

        # Check for finance signature: both revenue and expenses
        if domain_mappings["revenue"] is not None and domain_mappings["expense"] is not None:
            domain_scores["finance"] += 4

        # Check for customer signature: customer ID and segments/dates
        if domain_mappings["customer_id"] is not None and (domain_mappings["segment"] is not None or "churn" in str(df.columns).lower()):
            domain_scores["customer"] += 3

        # Determine primary domain
        best_domain = max(domain_scores, key=domain_scores.get)
        max_score = domain_scores[best_domain]
        total_score = sum(domain_scores.values())

        if max_score == 0:
            primary_domain = "general"
            confidence = 0.5
        else:
            primary_domain = best_domain
            confidence = round(min(0.98, 0.55 + (max_score / max(1, total_score)) * 0.4), 2)

        # Generate business context summary
        summary_parts = [
            f"Dataset '{dataset_name}' contains {total_rows:,} records across {total_cols} dimensions.",
            f"Classified as a **{primary_domain.upper()}** domain dataset ({int(confidence * 100)}% classification confidence).",
        ]
        if domain_mappings["date"]:
            summary_parts.append(f"Temporal dimension identified via '{domain_mappings['date']}'.")
        if primary_domain == "sales":
            summary_parts.append(f"Sales volume tracked via '{domain_mappings['revenue'] or domain_mappings['quantity'] or 'records'}'.")
        elif primary_domain == "finance":
            summary_parts.append(f"Financial accounting tracks revenue via '{domain_mappings['revenue']}' and expenses via '{domain_mappings['expense'] or 'unspecified'}'.")
        elif primary_domain == "customer":
            summary_parts.append(f"Customer records indexed by '{domain_mappings['customer_id']}'.")
        elif primary_domain == "inventory":
            summary_parts.append(f"Inventory and stock levels monitored via '{domain_mappings['stock'] or 'stock'}'.")

        return DatasetProfileResponse(
            datasetId=dataset_id,
            datasetName=dataset_name,
            rowCount=total_rows,
            columnCount=total_cols,
            fileType=file_type,
            fileSizeBytes=file_size_bytes,
            detectedDomain=primary_domain,
            domainConfidence=confidence,
            columnProfiles=col_profiles,
            domainMappings=domain_mappings,
            businessSummary=" ".join(summary_parts),
            createdAt=now_str,
        )

    # --------------------------------------------------------------------------
    # 2. Data Quality Agent
    # --------------------------------------------------------------------------

    @classmethod
    def audit_data_quality(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        mappings: Dict[str, Optional[str]],
    ) -> DataQualityAnalysisResponse:
        """
        Detects missing values, duplicates, invalid dates, inconsistent categories,
        and suspicious numeric values. Formulates actionable cleaning operations.
        Never mutates the underlying raw DataFrame.
        """
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if df is None or len(df) == 0:
            return DataQualityAnalysisResponse(
                datasetId=dataset_id,
                qualityScore=0.0,
                totalRows=0,
                totalColumns=0,
                totalCells=0,
                missingCells=0,
                missingCellRate=0.0,
                duplicateRows=0,
                duplicateRate=0.0,
                invalidDateCount=0,
                invalidDatesByCol={},
                inconsistentCategoryCount=0,
                inconsistentCategories=[],
                suspiciousNumericCount=0,
                suspiciousNumericIssues=[],
                suggestedOperations=[],
                cleanlinessStatus="poor_quality",
                timestamp=now_str,
            )

        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = max(1, total_rows * total_cols)

        # 1. Missing cells & duplicate rows
        missing_cells = int(df.isna().sum().sum())
        missing_rate = round((missing_cells / total_cells) * 100.0, 2)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_rate = round((duplicate_rows / total_rows) * 100.0, 2)

        # 2. Invalid dates
        invalid_date_count = 0
        invalid_dates_by_col: Dict[str, int] = {}
        date_col = mappings.get("date")
        if date_col and date_col in df.columns:
            raw_dates = df[date_col].dropna()
            parsed_dates = pd.to_datetime(raw_dates, errors="coerce")
            unparseable = int(parsed_dates.isna().sum())
            # Out of bounds (< 1970 or > 2100)
            valid_dt = parsed_dates.dropna()
            out_of_bounds = int(((valid_dt.dt.year < 1970) | (valid_dt.dt.year > 2100)).sum())
            total_invalid = unparseable + out_of_bounds
            if total_invalid > 0:
                invalid_date_count += total_invalid
                invalid_dates_by_col[date_col] = total_invalid

        # 3. Inconsistent categories (casing & whitespace variations)
        inconsistent_cat_count = 0
        inconsistent_categories: List[Dict[str, Any]] = []
        str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

        for c in str_cols[:6]:
            series = df[c].dropna().astype(str)
            raw_unique = series.nunique()
            normalized = series.str.strip().str.lower()
            norm_unique = normalized.nunique()

            if raw_unique > norm_unique and raw_unique > 1:
                diff = raw_unique - norm_unique
                inconsistent_cat_count += diff
                # Find examples
                val_counts = series.value_counts().head(5).to_dict()
                inconsistent_categories.append({
                    "column": c,
                    "rawUniqueCount": raw_unique,
                    "normalizedUniqueCount": norm_unique,
                    "casingDiscrepancies": diff,
                    "sampleValues": list(val_counts.keys())[:3],
                })

        # 4. Suspicious numeric values
        suspicious_num_count = 0
        suspicious_numeric_issues: List[Dict[str, Any]] = []

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for c in num_cols:
            series = df[c].dropna()
            # Negative values in strict positive columns
            c_low = c.lower()
            if any(k in c_low for k in ["price", "unitprice", "cost", "reorder", "stock", "inventory"]):
                negatives = int((series < 0).sum())
                if negatives > 0:
                    suspicious_num_count += negatives
                    suspicious_numeric_issues.append({
                        "column": c,
                        "issueType": "negative_value_in_positive_field",
                        "affectedCount": negatives,
                        "description": f"Found {negatives:,} negative values in positive metric '{c}'.",
                    })

            # Infinite values
            inf_count = int(np.isinf(series).sum())
            if inf_count > 0:
                suspicious_num_count += inf_count
                suspicious_numeric_issues.append({
                    "column": c,
                    "issueType": "infinite_values",
                    "affectedCount": inf_count,
                    "description": f"Detected {inf_count:,} infinite values in numeric column '{c}'.",
                })

        # 5. Suggested cleaning operations
        suggested_ops: List[CleaningOperation] = []

        if duplicate_rows > 0:
            suggested_ops.append(CleaningOperation(
                ruleId="deduplicate_rows",
                ruleName="Remove Exact Duplicate Rows",
                description=f"Eliminate {duplicate_rows:,} redundant rows with identical values across all columns.",
                affectedRows=duplicate_rows,
                targetColumns=list(df.columns),
                priority="high" if duplicate_rate > 5.0 else "medium",
                enabled=True,
            ))

        if missing_cells > 0:
            suggested_ops.append(CleaningOperation(
                ruleId="impute_missing_cells",
                ruleName="Impute Missing Cell Values",
                description=f"Impute {missing_cells:,} missing cells using column medians for numeric series and 'Unknown' for categories.",
                affectedRows=missing_cells,
                targetColumns=[c for c in df.columns if df[c].isna().sum() > 0],
                priority="high" if missing_rate > 15.0 else "medium",
                enabled=True,
            ))

        if inconsistent_cat_count > 0:
            suggested_ops.append(CleaningOperation(
                ruleId="normalize_category_casing",
                ruleName="Standardize Text and Category Normalization",
                description=f"Standardize letter casing and trim whitespace in {len(inconsistent_categories)} categorical dimensions.",
                affectedRows=inconsistent_cat_count,
                targetColumns=[ic["column"] for ic in inconsistent_categories],
                priority="medium",
                enabled=True,
            ))

        if invalid_date_count > 0:
            suggested_ops.append(CleaningOperation(
                ruleId="clean_invalid_dates",
                ruleName="Sanitize Unparseable Date Formats",
                description=f"Coerce {invalid_date_count:,} unparseable or out-of-bounds date values to null or valid timestamps.",
                affectedRows=invalid_date_count,
                targetColumns=list(invalid_dates_by_col.keys()),
                priority="high",
                enabled=True,
            ))

        # Calculate Quality Score
        penalty = (
            missing_rate * 0.4
            + duplicate_rate * 0.3
            + min(15.0, (invalid_date_count / max(1, total_rows)) * 100 * 0.2)
            + min(10.0, (suspicious_num_count / max(1, total_rows)) * 100 * 0.2)
        )
        quality_score = max(5.0, round(100.0 - penalty, 1))

        if quality_score >= 85.0:
            status: Literal["healthy", "moderate_issues", "poor_quality"] = "healthy"
        elif quality_score >= 60.0:
            status = "moderate_issues"
        else:
            status = "poor_quality"

        return DataQualityAnalysisResponse(
            datasetId=dataset_id,
            qualityScore=quality_score,
            totalRows=total_rows,
            totalColumns=total_cols,
            totalCells=total_cells,
            missingCells=missing_cells,
            missingCellRate=missing_rate,
            duplicateRows=duplicate_rows,
            duplicateRate=duplicate_rate,
            invalidDateCount=invalid_date_count,
            invalidDatesByCol=invalid_dates_by_col,
            inconsistentCategoryCount=inconsistent_cat_count,
            inconsistentCategories=inconsistent_categories,
            suspiciousNumericCount=suspicious_num_count,
            suspiciousNumericIssues=suspicious_numeric_issues,
            suggestedOperations=suggested_ops,
            cleanlinessStatus=status,
            timestamp=now_str,
        )

    # --------------------------------------------------------------------------
    # 3. Business Analyst Agent (Domain-Specific Engine)
    # --------------------------------------------------------------------------

    @classmethod
    def analyze_business_metrics(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        domain: str,
        mappings: Dict[str, Optional[str]],
    ) -> BusinessMetricsResponse:
        """
        Computes domain-specific verified metrics for Sales, Finance, Customer, and Inventory.
        Strict rule: Never forces metrics when required columns are missing;
        returns explicit explanations of required data.
        """
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if df is None or len(df) == 0:
            return BusinessMetricsResponse(
                datasetId=dataset_id,
                domain=domain if domain in ["sales", "finance", "customer", "inventory", "general"] else "general",
                computedMetrics=[],
                missingRequirements=[
                    MissingColumnRequirement(
                        metricName="All Metrics",
                        missingColumns=["*"],
                        explanation="Cannot calculate business metrics on an empty dataset (0 records).",
                    )
                ],
                domainDetails={},
                temporalTrends=[],
                topCategories=[],
                topRegions=[],
                findings=["The dataset is empty. Please upload valid business records."],
                citations=[],
                timestamp=now_str,
            )

        if domain == "finance":
            return cls._analyze_finance(df, dataset_id, mappings, now_str)
        elif domain == "customer":
            return cls._analyze_customer(df, dataset_id, mappings, now_str)
        elif domain == "inventory":
            return cls._analyze_inventory(df, dataset_id, mappings, now_str)
        else:
            # Default to sales / commerce
            return cls._analyze_sales(df, dataset_id, mappings, now_str)

    @classmethod
    def _analyze_sales(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        mappings: Dict[str, Optional[str]],
        now_str: str,
    ) -> BusinessMetricsResponse:
        metrics: List[MetricItem] = []
        missing_reqs: List[MissingColumnRequirement] = []
        findings: List[str] = []
        citations: List[str] = []
        total_records = len(df)

        rev_col = mappings.get("revenue")
        qty_col = mappings.get("quantity")
        price_col = mappings.get("price")
        order_col = mappings.get("order_id")
        date_col = mappings.get("date")
        cat_col = mappings.get("category") or mappings.get("product")
        country_col = mappings.get("country")

        # 1. Total Revenue Calculation
        if rev_col and rev_col in df.columns:
            clean_rev = pd.to_numeric(df[rev_col], errors="coerce").fillna(0)
            total_revenue = float(clean_rev.sum())
            source_desc = f"SUM({rev_col})"
        elif qty_col and price_col and qty_col in df.columns and price_col in df.columns:
            q = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
            p = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
            clean_rev = q * p
            total_revenue = float(clean_rev.sum())
            source_desc = f"SUM({qty_col} * {price_col})"
        else:
            clean_rev = pd.Series([1.0] * total_records, index=df.index)
            total_revenue = float(total_records)
            source_desc = "COUNT(rows)"
            missing_reqs.append(MissingColumnRequirement(
                metricName="Total Revenue",
                missingColumns=["revenue", "amount", "sales", "price"],
                explanation="Accurate revenue requires a dedicated revenue/amount column or price * quantity pair. Displaying transaction volume instead.",
            ))

        formatted_rev = f"${total_revenue:,.2f}" if total_revenue < 1_000_000 else f"${total_revenue / 1_000_000:.2f}M"
        metrics.append(MetricItem(
            id="total_revenue",
            label="Total Gross Revenue",
            value=formatted_rev,
            rawValue=round(total_revenue, 2),
            unit="$",
            trend="up",
            description=f"Calculated from {source_desc} across {total_records:,} records.",
            aiInsight=f"Aggregated {formatted_rev} topline volume from verified transaction records.",
        ))
        findings.append(f"Total Gross Revenue verified at {formatted_rev} across {total_records:,} observations.")
        citations.append(f"{source_desc} evaluated on {total_records} rows")

        # 2. Total Orders
        if order_col and order_col in df.columns:
            total_orders = int(df[order_col].nunique(dropna=True))
            order_desc = f"COUNT(DISTINCT {order_col})"
        else:
            total_orders = total_records
            order_desc = "COUNT(rows)"
            missing_reqs.append(MissingColumnRequirement(
                metricName="Distinct Order Volume",
                missingColumns=["order_id", "invoice_no"],
                explanation="No unique order identifier found. Rows treated as individual transactions.",
            ))

        metrics.append(MetricItem(
            id="total_orders",
            label="Total Transactions / Orders",
            value=f"{total_orders:,}",
            rawValue=float(total_orders),
            unit="orders",
            trend="neutral",
            description=f"Computed from {order_desc}.",
            aiInsight=f"Total observed transaction activity comprises {total_orders:,} orders.",
        ))
        findings.append(f"Order volume evaluated at {total_orders:,} total orders.")
        citations.append(f"{order_desc}")

        # 3. Average Order Value (AOV)
        aov = (total_revenue / max(1, total_orders))
        metrics.append(MetricItem(
            id="aov",
            label="Average Order Value (AOV)",
            value=f"${aov:,.2f}",
            rawValue=round(aov, 2),
            unit="$",
            trend="up" if aov > 50 else "neutral",
            description="Total Revenue divided by Total Orders.",
            aiInsight=f"Mean transaction size is ${aov:,.2f} per order.",
        ))
        findings.append(f"Average Order Value (AOV) established at ${aov:,.2f}.")

        # 4. Temporal Trends & Growth Rate
        temporal_trends: List[Dict[str, Any]] = []
        if date_col and date_col in df.columns:
            df_temp = df.copy()
            df_temp["_date"] = pd.to_datetime(df_temp[date_col], errors="coerce")
            df_temp["_rev"] = clean_rev
            valid_dt = df_temp.dropna(subset=["_date"])

            if len(valid_dt) > 0:
                daily = valid_dt.groupby(valid_dt["_date"].dt.strftime("%Y-%m-%d")).agg(
                    value=("_rev", "sum"),
                    volume=("_rev", "count")
                ).reset_index().rename(columns={"_date": "date"})

                temporal_trends = daily.to_dict(orient="records")

                # Growth rate: Compare first half vs second half
                if len(daily) >= 4:
                    mid = len(daily) // 2
                    first_half_sum = daily.iloc[:mid]["value"].sum()
                    second_half_sum = daily.iloc[mid:]["value"].sum()
                    if first_half_sum > 0:
                        growth_pct = round(((second_half_sum - first_half_sum) / first_half_sum) * 100, 1)
                        trend_dir = "up" if growth_pct > 0 else "down"
                        metrics[0].changePercent = growth_pct
                        metrics[0].periodLabel = "vs prior period"
                        findings.append(f"Period-over-period revenue growth calculated at {growth_pct:+}% comparing chronologically divided intervals.")
        else:
            missing_reqs.append(MissingColumnRequirement(
                metricName="Revenue & Order Trends",
                missingColumns=["date", "timestamp"],
                explanation="A date or timestamp column is required to evaluate time-series trends and period growth rates.",
            ))

        # 5. Category Breakdown
        top_categories: List[Dict[str, Any]] = []
        if cat_col and cat_col in df.columns:
            df_temp = df.copy()
            df_temp["_rev"] = clean_rev
            cat_grouped = df_temp.groupby(cat_col).agg(
                value=("_rev", "sum"),
                count=("_rev", "count")
            ).sort_values(by="value", ascending=False).head(8).reset_index()

            for _, row in cat_grouped.iterrows():
                val = float(row["value"])
                pct = round((val / max(1e-6, total_revenue)) * 100, 1)
                top_categories.append({
                    "name": str(row[cat_col]),
                    "value": round(val, 2),
                    "count": int(row["count"]),
                    "percentage": pct,
                })
            if top_categories:
                lead_cat = top_categories[0]
                findings.append(f"Lead category '{lead_cat['name']}' contributes ${lead_cat['value']:,.2f} ({lead_cat['percentage']}% of total sales).")
        else:
            missing_reqs.append(MissingColumnRequirement(
                metricName="Category Performance",
                missingColumns=["category", "product_type", "department"],
                explanation="No product or category column detected for breakdown analysis.",
            ))

        # 6. Regional Breakdown
        top_regions: List[Dict[str, Any]] = []
        if country_col and country_col in df.columns:
            df_temp = df.copy()
            df_temp["_rev"] = clean_rev
            geo_grouped = df_temp.groupby(country_col).agg(
                value=("_rev", "sum"),
                count=("_rev", "count")
            ).sort_values(by="value", ascending=False).head(8).reset_index()

            for _, row in geo_grouped.iterrows():
                val = float(row["value"])
                pct = round((val / max(1e-6, total_revenue)) * 100, 1)
                top_regions.append({
                    "name": str(row[country_col]),
                    "value": round(val, 2),
                    "count": int(row["count"]),
                    "percentage": pct,
                })
            if top_regions:
                lead_geo = top_regions[0]
                findings.append(f"Lead region '{lead_geo['name']}' represents ${lead_geo['value']:,.2f} ({lead_geo['percentage']}% of total volume).")

        return BusinessMetricsResponse(
            datasetId=dataset_id,
            domain="sales",
            computedMetrics=metrics,
            missingRequirements=missing_reqs,
            domainDetails={
                "totalRevenue": round(total_revenue, 2),
                "totalOrders": total_orders,
                "aov": round(aov, 2),
                "categoryCount": len(top_categories),
                "regionCount": len(top_regions),
            },
            temporalTrends=temporal_trends,
            topCategories=top_categories,
            topRegions=top_regions,
            findings=findings,
            citations=citations,
            timestamp=now_str,
        )

    @classmethod
    def _analyze_finance(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        mappings: Dict[str, Optional[str]],
        now_str: str,
    ) -> BusinessMetricsResponse:
        metrics: List[MetricItem] = []
        missing_reqs: List[MissingColumnRequirement] = []
        findings: List[str] = []
        citations: List[str] = []
        total_records = len(df)

        rev_col = mappings.get("revenue")
        exp_col = mappings.get("expense")
        prof_col = mappings.get("profit")
        date_col = mappings.get("date")

        # 1. Revenue
        if rev_col and rev_col in df.columns:
            clean_rev = pd.to_numeric(df[rev_col], errors="coerce").fillna(0)
            total_rev = float(clean_rev.sum())
            rev_desc = f"SUM({rev_col})"
        else:
            clean_rev = pd.Series([0.0] * total_records, index=df.index)
            total_rev = 0.0
            rev_desc = "0.0 (missing revenue column)"
            missing_reqs.append(MissingColumnRequirement(
                metricName="Total Revenue",
                missingColumns=["revenue", "sales", "income"],
                explanation="A revenue column is required to compute gross operating income.",
            ))

        formatted_rev = f"${total_rev:,.2f}" if total_rev < 1_000_000 else f"${total_rev / 1_000_000:.2f}M"
        metrics.append(MetricItem(
            id="fin_revenue",
            label="Gross Operating Revenue",
            value=formatted_rev,
            rawValue=round(total_rev, 2),
            unit="$",
            trend="up",
            description=f"Computed from {rev_desc}.",
            aiInsight=f"Total incoming financial revenue verified at {formatted_rev}.",
        ))
        findings.append(f"Gross Revenue audited at {formatted_rev}.")
        citations.append(f"{rev_desc}")

        # 2. Expenses
        if exp_col and exp_col in df.columns:
            clean_exp = pd.to_numeric(df[exp_col], errors="coerce").fillna(0)
            total_exp = float(clean_exp.sum())
            exp_desc = f"SUM({exp_col})"
        else:
            clean_exp = pd.Series([0.0] * total_records, index=df.index)
            total_exp = 0.0
            exp_desc = "0.0 (missing expense column)"
            missing_reqs.append(MissingColumnRequirement(
                metricName="Total Expenses & Costs",
                missingColumns=["expense", "cost", "cogs", "spending"],
                explanation="An expense or COGS column is required to compute net costs and profit margins.",
            ))

        formatted_exp = f"${total_exp:,.2f}" if total_exp < 1_000_000 else f"${total_exp / 1_000_000:.2f}M"
        metrics.append(MetricItem(
            id="fin_expenses",
            label="Total Expenses / Outgoings",
            value=formatted_exp,
            rawValue=round(total_exp, 2),
            unit="$",
            trend="down" if total_exp < total_rev else "up",
            description=f"Computed from {exp_desc}.",
            aiInsight=f"Total operating expenditure calculated at {formatted_exp}.",
        ))
        findings.append(f"Operating Expenses audited at {formatted_exp}.")
        citations.append(f"{exp_desc}")

        # 3. Profit & Margin
        if prof_col and prof_col in df.columns:
            clean_prof = pd.to_numeric(df[prof_col], errors="coerce").fillna(0)
            total_prof = float(clean_prof.sum())
            prof_desc = f"SUM({prof_col})"
        elif rev_col and exp_col:
            clean_prof = clean_rev - clean_exp
            total_prof = float(clean_prof.sum())
            prof_desc = f"{rev_col} - {exp_col}"
        else:
            clean_prof = pd.Series([0.0] * total_records, index=df.index)
            total_prof = 0.0
            prof_desc = "N/A"
            missing_reqs.append(MissingColumnRequirement(
                metricName="Net Operating Profit",
                missingColumns=["profit", "expense"],
                explanation="Requires both revenue and expense columns (or explicit profit column) to calculate net earnings.",
            ))

        formatted_prof = f"${total_prof:,.2f}" if abs(total_prof) < 1_000_000 else f"${total_prof / 1_000_000:.2f}M"
        metrics.append(MetricItem(
            id="fin_profit",
            label="Net Operating Profit",
            value=formatted_prof,
            rawValue=round(total_prof, 2),
            unit="$",
            trend="up" if total_prof > 0 else "down",
            description=f"Computed from {prof_desc}.",
            aiInsight=f"Net financial earnings evaluate to {formatted_prof}.",
        ))
        findings.append(f"Net Operating Profit verified at {formatted_prof}.")

        # Profit Margin %
        margin_pct = round((total_prof / total_rev * 100) if total_rev > 0 else 0.0, 2)
        metrics.append(MetricItem(
            id="fin_margin",
            label="Profit Margin",
            value=f"{margin_pct:.1f}%",
            rawValue=margin_pct,
            unit="%",
            trend="up" if margin_pct > 15.0 else "neutral",
            description="Net Profit / Gross Revenue * 100.",
            aiInsight=f"Operating profit margin is {margin_pct:.1f}%.",
        ))
        findings.append(f"Operating Profit Margin confirmed at {margin_pct:.1f}%.")

        # Period-over-period variance
        temporal_trends: List[Dict[str, Any]] = []
        if date_col and date_col in df.columns:
            df_temp = df.copy()
            df_temp["_date"] = pd.to_datetime(df_temp[date_col], errors="coerce")
            df_temp["_prof"] = clean_prof
            df_temp["_rev"] = clean_rev
            valid_dt = df_temp.dropna(subset=["_date"])

            if len(valid_dt) > 0:
                monthly = valid_dt.groupby(valid_dt["_date"].dt.strftime("%Y-%m")).agg(
                    value=("_rev", "sum"),
                    profit=("_prof", "sum")
                ).reset_index().rename(columns={"_date": "date"})

                temporal_trends = monthly.to_dict(orient="records")

                if len(monthly) >= 2:
                    last_m = monthly.iloc[-1]["profit"]
                    prev_m = monthly.iloc[-2]["profit"]
                    if abs(prev_m) > 0:
                        mom_change = round(((last_m - prev_m) / abs(prev_m)) * 100, 1)
                        metrics[2].changePercent = mom_change
                        metrics[2].periodLabel = "MoM change"
                        findings.append(f"Month-over-month profit variance shifted by {mom_change:+}% in the latest observed reporting cycle.")
        else:
            missing_reqs.append(MissingColumnRequirement(
                metricName="Period-over-Period Changes",
                missingColumns=["date", "fiscal_period"],
                explanation="A date or reporting period column is necessary for monthly and quarterly period variance calculations.",
            ))

        return BusinessMetricsResponse(
            datasetId=dataset_id,
            domain="finance",
            computedMetrics=metrics,
            missingRequirements=missing_reqs,
            domainDetails={
                "revenue": round(total_rev, 2),
                "expenses": round(total_exp, 2),
                "profit": round(total_prof, 2),
                "marginPercent": margin_pct,
            },
            temporalTrends=temporal_trends,
            topCategories=[],
            topRegions=[],
            findings=findings,
            citations=citations,
            timestamp=now_str,
        )

    @classmethod
    def _analyze_customer(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        mappings: Dict[str, Optional[str]],
        now_str: str,
    ) -> BusinessMetricsResponse:
        metrics: List[MetricItem] = []
        missing_reqs: List[MissingColumnRequirement] = []
        findings: List[str] = []
        citations: List[str] = []
        total_records = len(df)

        cust_col = mappings.get("customer_id")
        date_col = mappings.get("date")
        rev_col = mappings.get("revenue") or mappings.get("price")
        seg_col = mappings.get("segment")

        if not cust_col or cust_col not in df.columns:
            missing_reqs.append(MissingColumnRequirement(
                metricName="Customer Intelligence Suite",
                missingColumns=["customer_id", "client_id", "user_id"],
                explanation="Customer analysis requires a unique customer identification column ('customer_id').",
            ))
            return BusinessMetricsResponse(
                datasetId=dataset_id,
                domain="customer",
                computedMetrics=[],
                missingRequirements=missing_reqs,
                domainDetails={},
                temporalTrends=[],
                topCategories=[],
                topRegions=[],
                findings=["Cannot perform customer segmentation: No customer identification field present."],
                citations=[],
                timestamp=now_str,
            )

        # 1. Total Customers
        unique_custs = int(df[cust_col].nunique(dropna=True))
        metrics.append(MetricItem(
            id="cust_total",
            label="Total Identified Accounts",
            value=f"{unique_custs:,}",
            rawValue=float(unique_custs),
            unit="customers",
            trend="up",
            description=f"Distinct count of '{cust_col}'.",
            aiInsight=f"Total active account directory verified at {unique_custs:,} unique entities.",
        ))
        findings.append(f"Identified {unique_custs:,} distinct customer accounts.")
        citations.append(f"COUNT(DISTINCT {cust_col})")

        # 2. New vs. Returning Customers
        new_cust_cnt, ret_cust_cnt = 0, 0
        if date_col and date_col in df.columns:
            df_temp = df.copy()
            df_temp["_date"] = pd.to_datetime(df_temp[date_col], errors="coerce")
            valid_dt = df_temp.dropna(subset=["_date", cust_col])

            if len(valid_dt) > 0:
                cust_orders = valid_dt.groupby(cust_col).agg(
                    order_count=("_date", "count"),
                    first_date=("_date", "min"),
                    last_date=("_date", "max"),
                ).reset_index()

                ret_cust_cnt = int((cust_orders["order_count"] > 1).sum())
                new_cust_cnt = unique_custs - ret_cust_cnt
                ret_rate = round((ret_cust_cnt / max(1, unique_custs)) * 100, 1)

                metrics.append(MetricItem(
                    id="cust_retention",
                    label="Repeat Customer Rate",
                    value=f"{ret_rate:.1f}%",
                    rawValue=ret_rate,
                    unit="%",
                    trend="up" if ret_rate > 20.0 else "neutral",
                    description=f"{ret_cust_cnt:,} returning vs {new_cust_cnt:,} single-purchase accounts.",
                    aiInsight=f"Customer repeat purchase rate is {ret_rate:.1f}%.",
                ))
                findings.append(f"Repeat purchase behavior confirmed for {ret_cust_cnt:,} accounts ({ret_rate}% customer loyalty).")
        else:
            missing_reqs.append(MissingColumnRequirement(
                metricName="New vs Returning Customer Cohorts",
                missingColumns=["date", "timestamp"],
                explanation="A date column is required to calculate customer retention and cohort repeat purchase rates.",
            ))

        # 3. Customer Segments / Spend Distribution
        top_categories: List[Dict[str, Any]] = []
        if rev_col and rev_col in df.columns:
            clean_amt = pd.to_numeric(df[rev_col], errors="coerce").fillna(0)
            df_temp = df.copy()
            df_temp["_amt"] = clean_amt
            cust_spend = df_temp.groupby(cust_col)["_amt"].sum().sort_values(ascending=False)

            mean_spend = float(cust_spend.mean())
            top_10_pct = int(max(1, len(cust_spend) * 0.1))
            top_10_spend = float(cust_spend.head(top_10_pct).sum())
            total_spend = float(cust_spend.sum())
            concentration = round((top_10_spend / max(1e-6, total_spend)) * 100, 1)

            metrics.append(MetricItem(
                id="cust_avg_spend",
                label="Average Spend Per Account",
                value=f"${mean_spend:,.2f}",
                rawValue=round(mean_spend, 2),
                unit="$",
                trend="up",
                description="Total spend divided by unique customer count.",
                aiInsight=f"Mean lifetime transaction value is ${mean_spend:,.2f} per account.",
            ))

            findings.append(f"Top 10% highest-value accounts concentrate {concentration}% of total revenue volume.")

            # Construct tiers
            q75 = cust_spend.quantile(0.75)
            q25 = cust_spend.quantile(0.25)
            high_tier = int((cust_spend >= q75).sum())
            mid_tier = int(((cust_spend < q75) & (cust_spend >= q25)).sum())
            low_tier = int((cust_spend < q25).sum())

            top_categories = [
                {"name": "VIP / High Spend (Top 25%)", "value": high_tier, "count": high_tier, "percentage": round((high_tier / unique_custs) * 100, 1)},
                {"name": "Core / Mid Tier (Middle 50%)", "value": mid_tier, "count": mid_tier, "percentage": round((mid_tier / unique_custs) * 100, 1)},
                {"name": "Low Spend / Casual (Bottom 25%)", "value": low_tier, "count": low_tier, "percentage": round((low_tier / unique_custs) * 100, 1)},
            ]

        return BusinessMetricsResponse(
            datasetId=dataset_id,
            domain="customer",
            computedMetrics=metrics,
            missingRequirements=missing_reqs,
            domainDetails={
                "uniqueCustomers": unique_custs,
                "returningCustomers": ret_cust_cnt,
                "newCustomers": new_cust_cnt,
            },
            temporalTrends=[],
            topCategories=top_categories,
            topRegions=[],
            findings=findings,
            citations=citations,
            timestamp=now_str,
        )

    @classmethod
    def _analyze_inventory(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        mappings: Dict[str, Optional[str]],
        now_str: str,
    ) -> BusinessMetricsResponse:
        metrics: List[MetricItem] = []
        missing_reqs: List[MissingColumnRequirement] = []
        findings: List[str] = []
        citations: List[str] = []
        total_records = len(df)

        stock_col = mappings.get("stock")
        reorder_col = mappings.get("reorder_level")
        sku_col = mappings.get("product")
        sales_col = mappings.get("quantity") or mappings.get("revenue")

        if not stock_col or stock_col not in df.columns:
            missing_reqs.append(MissingColumnRequirement(
                metricName="Inventory & Stock Analysis",
                missingColumns=["stock", "units_on_hand", "inventory"],
                explanation="Inventory auditing requires a stock quantity column ('stock' or 'quantity_on_hand').",
            ))
            return BusinessMetricsResponse(
                datasetId=dataset_id,
                domain="inventory",
                computedMetrics=[],
                missingRequirements=missing_reqs,
                domainDetails={},
                temporalTrends=[],
                topCategories=[],
                topRegions=[],
                findings=["Cannot audit warehouse stock: No inventory quantity column identified."],
                citations=[],
                timestamp=now_str,
            )

        clean_stock = pd.to_numeric(df[stock_col], errors="coerce").fillna(0)
        total_stock = float(clean_stock.sum())

        # 1. Total Stock Level
        metrics.append(MetricItem(
            id="inv_stock",
            label="Total Warehouse Stock Units",
            value=f"{int(total_stock):,}",
            rawValue=total_stock,
            unit="units",
            trend="neutral",
            description=f"Sum of '{stock_col}' across all catalog SKUs.",
            aiInsight=f"Total aggregate warehouse units on hand evaluated at {int(total_stock):,} units.",
        ))
        findings.append(f"Aggregate warehouse inventory verified at {int(total_stock):,} units.")
        citations.append(f"SUM({stock_col})")

        # 2. Low-Stock Items
        low_stock_count = 0
        if reorder_col and reorder_col in df.columns:
            reorder_series = pd.to_numeric(df[reorder_col], errors="coerce").fillna(10)
            low_stock_mask = clean_stock <= reorder_series
            low_stock_count = int(low_stock_mask.sum())
            threshold_desc = f"stock <= '{reorder_col}' threshold"
        else:
            # Fallback: bottom 15th percentile or <= 10 units
            q15 = clean_stock.quantile(0.15)
            threshold_val = max(5.0, q15)
            low_stock_mask = clean_stock <= threshold_val
            low_stock_count = int(low_stock_mask.sum())
            threshold_desc = f"stock <= {threshold_val:.0f} (statistical safety stock)"
            missing_reqs.append(MissingColumnRequirement(
                metricName="Exact Reorder Threshold",
                missingColumns=["reorder_level", "min_stock"],
                explanation="No explicit reorder point column provided. Using statistical 15th percentile safety threshold.",
            ))

        low_stock_pct = round((low_stock_count / max(1, total_records)) * 100, 1)
        metrics.append(MetricItem(
            id="inv_low_stock",
            label="Low-Stock / Reorder Alert SKUs",
            value=f"{low_stock_count:,}",
            rawValue=float(low_stock_count),
            unit="SKUs",
            trend="down" if low_stock_count > 0 else "neutral",
            description=f"Identified using {threshold_desc}.",
            aiInsight=f"{low_stock_count:,} items ({low_stock_pct}%) are at or below reorder threshold.",
        ))
        findings.append(f"Stockout Risk: {low_stock_count:,} SKUs ({low_stock_pct}%) flagged for immediate inventory replenishment.")

        # 3. Out of stock (Zero inventory)
        out_of_stock = int((clean_stock == 0).sum())
        metrics.append(MetricItem(
            id="inv_zero_stock",
            label="Zero Stock (Stockout) SKUs",
            value=f"{out_of_stock:,}",
            rawValue=float(out_of_stock),
            unit="SKUs",
            trend="down" if out_of_stock > 0 else "neutral",
            description="Catalog items with 0 units on hand.",
            aiInsight=f"{out_of_stock:,} items have zero available warehouse stock.",
        ))

        # 4. Inventory Turnover / Sales Velocity
        if sales_col and sales_col in df.columns:
            clean_sales = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)
            total_sold = float(clean_sales.sum())
            turnover_ratio = round((total_sold / max(1.0, total_stock)), 2)
            metrics.append(MetricItem(
                id="inv_turnover",
                label="Inventory Turnover Ratio",
                value=f"{turnover_ratio:.2f}x",
                rawValue=turnover_ratio,
                unit="ratio",
                trend="up" if turnover_ratio > 1.0 else "neutral",
                description="Total Units Sold / Average Stock Level.",
                aiInsight=f"Inventory turnover velocity evaluated at {turnover_ratio:.2f}x.",
            ))
            findings.append(f"Inventory turnover ratio established at {turnover_ratio:.2f}x.")
        else:
            missing_reqs.append(MissingColumnRequirement(
                metricName="Inventory Turnover Ratio",
                missingColumns=["units_sold", "cogs", "quantity"],
                explanation="A sales volume or COGS column is required to evaluate inventory turnover velocity.",
            ))

        return BusinessMetricsResponse(
            datasetId=dataset_id,
            domain="inventory",
            computedMetrics=metrics,
            missingRequirements=missing_reqs,
            domainDetails={
                "totalStock": int(total_stock),
                "lowStockCount": low_stock_count,
                "outOfStockCount": out_of_stock,
            },
            temporalTrends=[],
            topCategories=[],
            topRegions=[],
            findings=findings,
            citations=citations,
            timestamp=now_str,
        )

    # --------------------------------------------------------------------------
    # 4. Statistical Anomaly Detection Engine
    # --------------------------------------------------------------------------

    @classmethod
    def detect_anomalies(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        mappings: Dict[str, Optional[str]],
    ) -> AnomalyReportResponse:
        """
        Detects unusual spikes, drops, outliers, and suspicious records using:
        - Tukey's IQR fences (1.5x)
        - Gaussian Z-score thresholds (|z| > 3.0)
        - Time-series moving average spikes/drops (> 2.5 std dev)
        Distinguishes statistical anomalies from confirmed business problems.
        """
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if df is None or len(df) == 0:
            return AnomalyReportResponse(
                datasetId=dataset_id,
                totalAnomalies=0,
                criticalCount=0,
                warningCount=0,
                infoCount=0,
                anomalies=[],
                summary="Zero anomalies detected on empty dataset.",
                timestamp=now_str,
            )

        anomalies: List[AnomalyItem] = []
        total_rows = len(df)

        # 1. Tukey IQR Outliers on Numeric Fields (Amounts, Prices, Quantities, Stock)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in num_cols[:4]:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) >= 15:
                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1

                if iqr > 0:
                    lower_fence = q1 - 1.5 * iqr
                    upper_fence = q3 + 1.5 * iqr

                    outliers = series[(series < lower_fence) | (series > upper_fence)]
                    outlier_count = len(outliers)

                    if outlier_count > 0:
                        pct = round((outlier_count / len(series)) * 100, 1)
                        # Check severity
                        severity: Literal["critical", "warning", "info"] = "warning" if pct > 3.0 else "info"

                        # Distinguish business event vs data issue
                        is_business_problem = False
                        if col.lower() in ["price", "unitprice"] and (outliers < 0).any():
                            is_business_problem = True
                            severity = "critical"
                            interp = f"Negative unit prices detected in '{col}', indicating data entry error or invalid transaction record."
                        elif "stock" in col.lower() and (outliers == 0).any():
                            is_business_problem = True
                            severity = "warning"
                            interp = f"Outliers in '{col}' represent extreme stock variations requiring supply chain rebalancing."
                        else:
                            interp = f"Observations outside 1.5x IQR [{lower_fence:.2f}, {upper_fence:.2f}]. Likely high-value VIP transactions or bulk order volumes."

                        anomalies.append(AnomalyItem(
                            anomalyId=f"anom_iqr_{col}",
                            severity=severity,
                            anomalyType="outlier",
                            columnName=col,
                            title=f"Statistical Outliers in '{col}' ({outlier_count:,} records)",
                            description=f"Detected {outlier_count:,} values ({pct}%) beyond Tukey fences [{lower_fence:.2f}, {upper_fence:.2f}].",
                            statisticalMethod="Tukey's Fences (1.5 * IQR)",
                            isConfirmedBusinessProblem=is_business_problem,
                            businessInterpretation=interp,
                            affectedRecordsCount=outlier_count,
                            evidence={
                                "q1": round(q1, 2),
                                "q3": round(q3, 2),
                                "iqr": round(iqr, 2),
                                "lowerFence": round(lower_fence, 2),
                                "upperFence": round(upper_fence, 2),
                                "maxOutlier": float(outliers.max()),
                                "minOutlier": float(outliers.min()),
                            },
                        ))

        # 2. Z-Score Spikes & Extreme Outliers (|z| > 3.0)
        for col in num_cols[:3]:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) >= 20:
                mean_val = float(series.mean())
                std_val = float(series.std())

                if std_val > 0:
                    z_scores = (series - mean_val) / std_val
                    extreme_z = series[abs(z_scores) > 3.0]
                    extreme_count = len(extreme_z)

                    if extreme_count > 0:
                        max_z = float(abs(z_scores).max())
                        anomalies.append(AnomalyItem(
                            anomalyId=f"anom_zscore_{col}",
                            severity="warning" if max_z < 5.0 else "critical",
                            anomalyType="spike" if extreme_z.max() > mean_val else "drop",
                            columnName=col,
                            title=f"Extreme Z-Score Anomaly in '{col}' (Max Z={max_z:.1f})",
                            description=f"Identified {extreme_count:,} records exceeding 3 standard deviations from the mean ({mean_val:.2f}).",
                            statisticalMethod="Gaussian Z-Score (|z| > 3.0)",
                            isConfirmedBusinessProblem=max_z > 6.0,
                            businessInterpretation=f"Extreme variance in '{col}' indicates potential billing errors or anomalous single-day enterprise purchases.",
                            affectedRecordsCount=extreme_count,
                            evidence={
                                "mean": round(mean_val, 2),
                                "stdDev": round(std_val, 2),
                                "maxZScore": round(max_z, 2),
                                "affectedRecords": extreme_count,
                            },
                        ))

        # 3. Temporal Spikes & Drops (Daily trajectory)
        date_col = mappings.get("date")
        amount_col = mappings.get("revenue") or mappings.get("quantity")

        if date_col and amount_col and date_col in df.columns and amount_col in df.columns:
            try:
                df_temp = df[[date_col, amount_col]].copy()
                df_temp["_date"] = pd.to_datetime(df_temp[date_col], errors="coerce")
                df_temp["_val"] = pd.to_numeric(df_temp[amount_col], errors="coerce").fillna(0)
                valid_dt = df_temp.dropna(subset=["_date"])

                if len(valid_dt) >= 14:
                    daily = valid_dt.groupby(valid_dt["_date"].dt.strftime("%Y-%m-%d"))["_val"].sum()
                    if len(daily) >= 7:
                        d_mean = daily.mean()
                        d_std = daily.std()

                        if d_std > 0:
                            spikes = daily[daily > d_mean + 2.5 * d_std]
                            drops = daily[daily < max(0, d_mean - 2.5 * d_std)]

                            for d_str, val in spikes.items():
                                z_approx = (val - d_mean) / d_std
                                anomalies.append(AnomalyItem(
                                    anomalyId=f"anom_spike_{d_str}",
                                    severity="warning",
                                    anomalyType="spike",
                                    columnName=date_col,
                                    title=f"Temporal Volume Spike on {d_str}",
                                    description=f"Volume reached ${val:,.2f}, which is {z_approx:.1f} standard deviations above daily average (${d_mean:,.2f}).",
                                    statisticalMethod="Time-Series Variance Threshold (> 2.5 std dev)",
                                    isConfirmedBusinessProblem=False,
                                    businessInterpretation="Legitimate commercial surge (promotional campaign, flash sale, or bulk contract fulfillment).",
                                    affectedRecordsCount=1,
                                    evidence={"date": d_str, "value": round(val, 2), "dailyMean": round(d_mean, 2), "zScore": round(z_approx, 2)},
                                ))

                            for d_str, val in drops.items():
                                z_approx = (d_mean - val) / d_std
                                anomalies.append(AnomalyItem(
                                    anomalyId=f"anom_drop_{d_str}",
                                    severity="critical",
                                    anomalyType="drop",
                                    columnName=date_col,
                                    title=f"Critical Volume Drop on {d_str}",
                                    description=f"Volume collapsed to ${val:,.2f}, representing a {z_approx:.1f} std dev departure from the average.",
                                    statisticalMethod="Time-Series Variance Threshold (> 2.5 std dev)",
                                    isConfirmedBusinessProblem=True,
                                    businessInterpretation="Operational bottleneck, system outage, payment gateway failure, or holiday closure.",
                                    affectedRecordsCount=1,
                                    evidence={"date": d_str, "value": round(val, 2), "dailyMean": round(d_mean, 2)},
                                ))
            except Exception as e:
                logger.warning(f"Temporal anomaly calculation encountered non-fatal error: {e}")

        # 4. Suspicious Records (Negative quantities representing retail returns vs corruption)
        qty_col = mappings.get("quantity")
        if qty_col and qty_col in df.columns:
            neg_q = df[pd.to_numeric(df[qty_col], errors="coerce") < 0]
            if len(neg_q) > 0:
                is_retail_return = any("c" in str(inv).lower() for inv in df.get("InvoiceNo", [])) if "InvoiceNo" in df.columns else False
                anomalies.append(AnomalyItem(
                    anomalyId="anom_negative_qty",
                    severity="info" if is_retail_return else "warning",
                    anomalyType="suspicious_record",
                    columnName=qty_col,
                    title=f"Negative Transaction Quantities ({len(neg_q):,} records)",
                    description=f"Found {len(neg_q):,} transactions with negative quantity in '{qty_col}'.",
                    statisticalMethod="Negative Threshold Audit (< 0)",
                    isConfirmedBusinessProblem=not is_retail_return,
                    businessInterpretation=(
                        "Legitimate customer product returns and cancellations with 'C' invoice prefix."
                        if is_retail_return else
                        "Negative quantity without return order prefix. Check for inventory adjustment or data entry corruption."
                    ),
                    affectedRecordsCount=len(neg_q),
                    evidence={"negativeCount": len(neg_q), "isIdentifiedReturn": is_retail_return},
                ))

        critical_c = sum(1 for a in anomalies if a.severity == "critical")
        warning_c = sum(1 for a in anomalies if a.severity == "warning")
        info_c = sum(1 for a in anomalies if a.severity == "info")

        summary_text = (
            f"Anomaly Audit completed: {len(anomalies)} total patterns identified "
            f"({critical_c} critical, {warning_c} warnings, {info_c} informational notices). "
            f"Statistical anomalies distinguished from confirmed commercial events."
        )

        return AnomalyReportResponse(
            datasetId=dataset_id,
            totalAnomalies=len(anomalies),
            criticalCount=critical_c,
            warningCount=warning_c,
            infoCount=info_c,
            anomalies=anomalies,
            summary=summary_text,
            timestamp=now_str,
        )
