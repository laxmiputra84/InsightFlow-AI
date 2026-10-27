from typing import List
from sqlalchemy.orm import Session
from app.models.kpi import KpiMetricModel


class KpiService:
    @staticmethod
    def get_kpis(db: Session, range_type: str = "30d") -> List[KpiMetricModel]:
        """
        Retrieves KPI metrics for the specified date range.
        If the range doesn't have distinct records, falls back to 30d baseline.
        """
        kpis = db.query(KpiMetricModel).filter(KpiMetricModel.range_type == range_type).all()
        if not kpis and range_type != "30d":
            kpis = db.query(KpiMetricModel).filter(KpiMetricModel.range_type == "30d").all()
        return kpis
