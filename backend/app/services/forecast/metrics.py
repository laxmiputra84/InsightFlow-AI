import math
from typing import List


class ForecastMetrics:
    """
    Standardized, safe out-of-sample error metric calculations
    for time-series forecasting.
    """

    @staticmethod
    def mae(actual: List[float], predicted: List[float]) -> float:
        """Mean Absolute Error (MAE): average magnitude of errors."""
        if not actual or not predicted or len(actual) != len(predicted):
            return 0.0
        n = len(actual)
        return round(sum(abs(a - p) for a, p in zip(actual, predicted)) / n, 2)

    @staticmethod
    def rmse(actual: List[float], predicted: List[float]) -> float:
        """Root Mean Squared Error (RMSE): penalizes larger deviations."""
        if not actual or not predicted or len(actual) != len(predicted):
            return 0.0
        n = len(actual)
        mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / n
        return round(math.sqrt(mse), 2)

    @staticmethod
    def mape(actual: List[float], predicted: List[float], epsilon: float = 1.0) -> float:
        """
        Mean Absolute Percentage Error (MAPE) in percentage points.
        Includes epsilon safeguarding against zero and near-zero actual values.
        """
        if not actual or not predicted or len(actual) != len(predicted):
            return 0.0
        n = len(actual)
        pct_errors = [
            abs(a - p) / max(abs(a), epsilon)
            for a, p in zip(actual, predicted)
        ]
        return round((sum(pct_errors) / n) * 100.0, 2)
