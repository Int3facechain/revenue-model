from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

import httpx
import pandas as pd


class BinanceFuturesFundingClient:
    DEFAULT_BASE_URL = "https://fapi.binance.com"

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
            self.client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def close(self) -> None:
        self.client.close()

    def get_funding_rate_history(
        self,
        symbol: str,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        if (
            start_time_ms is not None
            and end_time_ms is not None
            and start_time_ms > end_time_ms
        ):
            raise ValueError("start_time_ms must be <= end_time_ms")

        endpoint = "/fapi/v1/fundingRate"
        base_params: Dict[str, Any] = {
            "symbol": symbol,
            "limit": limit,
        }

        rows: List[Dict[str, Any]] = []

        if start_time_ms is None and end_time_ms is None:
            params = dict(base_params)
            data = self._request(endpoint, params)
            rows.extend(data)
        else:
            current_start = start_time_ms
            while True:
                params = dict(base_params)
                if current_start is not None:
                    params["startTime"] = current_start
                if end_time_ms is not None:
                    params["endTime"] = end_time_ms

                batch = self._request(endpoint, params)
                if not batch:
                    break

                rows.extend(batch)

                if len(batch) < limit:
                    break

                last_time = max(int(item["fundingTime"]) for item in batch)
                next_start = last_time + 1
                if end_time_ms is not None and next_start > end_time_ms:
                    break
                current_start = next_start

        if not rows:
            return pd.DataFrame(
                columns=[
                    "symbol",
                    "funding_time",
                    "funding_rate",
                    "funding_rate_bps",
                    "mark_price",
                ]
            )

        df = pd.DataFrame(rows)

        df["funding_time"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True)
        df["funding_rate"] = df["fundingRate"].astype(float)

        if "markPrice" in df.columns:
            df["mark_price"] = df["markPrice"].astype(float)
        else:
            df["mark_price"] = pd.NA

        df["funding_rate_bps"] = df["funding_rate"] * 10000.0

        df = df[
            [
                "symbol",
                "funding_time",
                "funding_rate",
                "funding_rate_bps",
                "mark_price",
            ]
        ].sort_values("funding_time")

        df.reset_index(drop=True, inplace=True)
        return df

    def _request(self, endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        resp = self.client.get(endpoint, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise RuntimeError("Unexpected response format from Binance")
        return data


class BinanceClient(BinanceFuturesFundingClient):
    """
    Thin adapter to match the dashboard API:

    get_funding_history(symbol: str, start_time: datetime, end_time: Optional[datetime])
    """

    @staticmethod
    def _to_millis(dt: datetime) -> int:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    def get_funding_history(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        start_ms = self._to_millis(start_time)
        end_ms = self._to_millis(end_time) if end_time is not None else None

        return super().get_funding_rate_history(
            symbol=symbol,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            limit=limit,
        )
