from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import time
import httpx
import pandas as pd


class DeriveFundingClient:
    """
    Minimal client for Derive funding rate history
    (public/get_funding_rate_history).
    """

    DEFAULT_BASE_URL = "https://api.lyra.finance"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 5.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout

        if client is not None:
            self.client = client
        else:
            self.client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

    def close(self) -> None:
        self.client.close()

    def get_funding_rate_history(
        self,
        instrument_name: str,
        start_timestamp_ms: Optional[int] = None,
        end_timestamp_ms: Optional[int] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch funding rate history for a Derive perpetual instrument.

        Parameters
        ----------
        instrument_name : str
            Instrument name, for example "BTC-PERP".
        start_timestamp_ms : Optional[int]
            Start time in milliseconds since epoch.
        end_timestamp_ms : Optional[int]
            End time in milliseconds since epoch.
        period : Optional[str]
            Optional period for the funding rate, as a string enum.
            Allowed values per docs:
            "900", "3600", "14400", "28800", "86400".
            By default we do not send this field.
        """
        if end_timestamp_ms is None:
            end_timestamp_ms = int(time.time() * 1000)

        if start_timestamp_ms is None:
            start_timestamp_ms = 0

        if start_timestamp_ms < 0:
            raise ValueError("start_timestamp_ms must be non-negative")

        if start_timestamp_ms > end_timestamp_ms:
            raise ValueError("start_timestamp_ms must be <= end_timestamp_ms")

        payload: Dict[str, Any] = {
            "instrument_name": instrument_name,
            "start_timestamp": int(start_timestamp_ms),
            "end_timestamp": int(end_timestamp_ms),
        }

        period_value: Optional[int] = None
        if period is not None:
            payload["period"] = str(period)
            try:
                period_value = int(period)
            except (TypeError, ValueError):
                period_value = None

        data = self._post("/public/get_funding_rate_history", payload)

        result = data.get("result") if isinstance(data, dict) else None
        history: Optional[List[Dict[str, Any]]] = None
        if isinstance(result, dict):
            history = result.get("funding_rate_history")

        if not history:
            return pd.DataFrame(
                columns=[
                    "instrument_name",
                    "time",
                    "funding_rate",
                    "funding_rate_bps",
                    "period_sec",
                ]
            )

        df = pd.DataFrame(history)

        df["time"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df["funding_rate"] = df["funding_rate"].astype(float)
        df["funding_rate_bps"] = df["funding_rate"] * 10000.0
        df["instrument_name"] = instrument_name
        df["period_sec"] = period_value

        df = df[
            [
                "instrument_name",
                "time",
                "funding_rate",
                "funding_rate_bps",
                "period_sec",
            ]
        ].sort_values("time")

        df.reset_index(drop=True, inplace=True)
        return df

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Any:
        resp = self.client.post(endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()


class DerivClient(DeriveFundingClient):
    """
    Thin adapter to match the dashboard API:

    get_funding_history(
        instrument_name: str,
        start_time: datetime,
        end_time: Optional[datetime],
        period: Optional[str] = None,
    )
    """

    @staticmethod
    def _to_millis(dt: datetime) -> int:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    def get_funding_history(
        self,
        instrument_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        start_ms = self._to_millis(start_time)
        end_ms = self._to_millis(end_time) if end_time is not None else None

        return super().get_funding_rate_history(
            instrument_name=instrument_name,
            start_timestamp_ms=start_ms,
            end_timestamp_ms=end_ms,
            period=period,
        )
