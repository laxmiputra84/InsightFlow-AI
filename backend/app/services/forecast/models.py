import math
from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseForecaster(ABC):
    """Abstract base class for all forecasting algorithms."""

    def __init__(self, name: str):
        self.name = name
        self.fitted_series: List[float] = []
        self.residual_std: float = 0.0

    @abstractmethod
    def fit(self, series: List[float]) -> "BaseForecaster":
        """Fits the model on a historical numerical series."""
        pass

    @abstractmethod
    def predict(self, horizon: int) -> List[float]:
        """Generates point forecasts for the specified horizon."""
        pass

    def get_prediction_intervals(
        self,
        point_forecasts: List[float],
        confidence: float = 0.95,
    ) -> List[Tuple[float, float]]:
        """
        Calculates symmetric (lower, upper) prediction intervals for forecasted points.
        Z-factor approximates normal distribution (95% -> 1.96, 80% -> 1.28).
        """
        z = 1.96 if confidence >= 0.90 else (1.645 if confidence >= 0.80 else 1.28)
        intervals = []
        base_std = max(self.residual_std, 1.0)

        for step, fc in enumerate(point_forecasts, start=1):
            # Variance expands with the forecast horizon square root factor
            step_std = base_std * math.sqrt(1.0 + 0.08 * step)
            margin = z * step_std
            lower = max(0.0, round(fc - margin, 2))
            upper = round(fc + margin, 2)
            intervals.append((lower, upper))

        return intervals


class NaiveForecaster(BaseForecaster):
    """
    Naive baseline model.
    Forecasts all future steps as the last observed value in the historical series.
    """

    def __init__(self):
        super().__init__("Naive Baseline")
        self.last_value: float = 0.0

    def fit(self, series: List[float]) -> "NaiveForecaster":
        if not series:
            raise ValueError("Cannot fit NaiveForecaster on empty series.")
        self.fitted_series = list(series)
        self.last_value = series[-1]

        # In-sample residuals for naive model: y_t - y_{t-1}
        if len(series) > 1:
            diffs = [series[i] - series[i - 1] for i in range(1, len(series))]
            var = sum(d ** 2 for d in diffs) / (len(diffs) or 1)
            self.residual_std = math.sqrt(var)
        else:
            self.residual_std = 1.0
        return self

    def predict(self, horizon: int) -> List[float]:
        return [round(self.last_value, 2) for _ in range(horizon)]


class MovingAverageForecaster(BaseForecaster):
    """
    Simple Moving Average (SMA) forecaster.
    Smooths high-frequency noise using a rolling window (default: 7 periods).
    """

    def __init__(self, window_size: int = 7):
        super().__init__(f"Moving Average (k={window_size})")
        self.window_size = window_size
        self.mean_forecast: float = 0.0

    def fit(self, series: List[float]) -> "MovingAverageForecaster":
        if len(series) < self.window_size:
            self.window_size = max(1, len(series))
            self.name = f"Moving Average (k={self.window_size})"

        self.fitted_series = list(series)
        window = series[-self.window_size :]
        self.mean_forecast = sum(window) / len(window)

        # In-sample residuals
        residuals = []
        for i in range(self.window_size, len(series)):
            w = series[i - self.window_size : i]
            pred = sum(w) / len(w)
            residuals.append(series[i] - pred)

        if residuals:
            var = sum(r ** 2 for r in residuals) / len(residuals)
            self.residual_std = math.sqrt(var)
        else:
            self.residual_std = 1.0
        return self

    def predict(self, horizon: int) -> List[float]:
        return [round(self.mean_forecast, 2) for _ in range(horizon)]


class LinearTrendForecaster(BaseForecaster):
    """
    Linear Trend Regression model (Ordinary Least Squares).
    Captures constant upward/downward slope: y_t = alpha + beta * t.
    """

    def __init__(self):
        super().__init__("Linear Trend (OLS)")
        self.alpha: float = 0.0
        self.beta: float = 0.0
        self.t_mean: float = 0.0
        self.denom: float = 1.0
        self.n: int = 0

    def fit(self, series: List[float]) -> "LinearTrendForecaster":
        n = len(series)
        if n < 2:
            raise ValueError("LinearTrendForecaster requires at least 2 points.")
        self.n = n
        self.fitted_series = list(series)

        t_vals = list(range(1, n + 1))
        self.t_mean = sum(t_vals) / n
        y_mean = sum(series) / n

        num = sum((t - self.t_mean) * (y - y_mean) for t, y in zip(t_vals, series))
        self.denom = sum((t - self.t_mean) ** 2 for t in t_vals) or 1.0

        self.beta = num / self.denom
        self.alpha = y_mean - self.beta * self.t_mean

        # Residual standard error
        residuals = [series[i] - (self.alpha + self.beta * (i + 1)) for i in range(n)]
        dof = max(1, n - 2)
        var = sum(r ** 2 for r in residuals) / dof
        self.residual_std = math.sqrt(var)
        return self

    def predict(self, horizon: int) -> List[float]:
        predictions = []
        for h in range(1, horizon + 1):
            t_future = self.n + h
            pred = max(0.0, self.alpha + self.beta * t_future)
            predictions.append(round(pred, 2))
        return predictions

    def get_prediction_intervals(
        self,
        point_forecasts: List[float],
        confidence: float = 0.95,
    ) -> List[Tuple[float, float]]:
        """Exact OLS standard error of prediction."""
        z = 1.96 if confidence >= 0.90 else (1.645 if confidence >= 0.80 else 1.28)
        s = max(self.residual_std, 1.0)
        intervals = []

        for h, fc in enumerate(point_forecasts, start=1):
            t_future = self.n + h
            # Standard error of forecast formula: s * sqrt(1 + 1/n + (t0 - t_bar)^2 / sum((t - t_bar)^2))
            se_pred = s * math.sqrt(1.0 + (1.0 / self.n) + ((t_future - self.t_mean) ** 2) / self.denom)
            margin = z * se_pred
            lower = max(0.0, round(fc - margin, 2))
            upper = round(fc + margin, 2)
            intervals.append((lower, upper))

        return intervals


class HoltLinearForecaster(BaseForecaster):
    """
    Double Exponential Smoothing (Holt's Linear Trend).
    Adapts both changing baseline level (alpha) and dynamic slope (beta).
    """

    def __init__(self, alpha: float = 0.3, beta: float = 0.15):
        super().__init__("Holt's Exponential Smoothing")
        self.alpha_param = alpha
        self.beta_param = beta
        self.level: float = 0.0
        self.trend: float = 0.0

    def fit(self, series: List[float]) -> "HoltLinearForecaster":
        n = len(series)
        if n < 2:
            raise ValueError("HoltLinearForecaster requires at least 2 points.")
        self.fitted_series = list(series)

        # Initialize level and trend from first two observations
        self.level = series[0]
        self.trend = series[1] - series[0]

        residuals = []
        for i in range(1, n):
            val = series[i]
            # One-step-ahead prediction: level_{t-1} + trend_{t-1}
            pred = self.level + self.trend
            residuals.append(val - pred)

            # Update level and trend
            last_level = self.level
            self.level = self.alpha_param * val + (1.0 - self.alpha_param) * (self.level + self.trend)
            self.trend = self.beta_param * (self.level - last_level) + (1.0 - self.beta_param) * self.trend

        if residuals:
            var = sum(r ** 2 for r in residuals) / len(residuals)
            self.residual_std = math.sqrt(var)
        else:
            self.residual_std = 1.0
        return self

    def predict(self, horizon: int) -> List[float]:
        predictions = []
        for h in range(1, horizon + 1):
            pred = max(0.0, self.level + h * self.trend)
            predictions.append(round(pred, 2))
        return predictions
