from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

import httpx
import pandas as pd


class HyperliquidInfoClient:
    """
    Minimal client for Hyperliquid perpetuals info endpoint,
    focused on funding data for arbitrage use cases.
    """

    DEFAULT_BASE_URL = "https://api.hyperliquid.xyz"

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

    def get_predicted_funding(self) -> pd.DataFrame:
        """
        Fetch predicted funding rates for all assets and venues.

        Returns
        -------
        pd.DataFrame
            Columns:
            - asset: str (e.g. "BTC")
            - venue: str ("HlPerp", "BinPerp", "BybitPerp", ...)
            - funding_rate: float
            - funding_rate_bps: float
            - next_funding_time: datetime64[ns, UTC]
        """
        payload: Dict[str, Any] = {"type": "predictedFundings"}
        data = self._post("/info", payload)

        rows: List[Dict[str, Any]] = []

        for entry in data:
            if not isinstance(entry, list) or len(entry) != 2:
                continue

            asset = entry[0]
            venues = entry[1]

            for venue_entry in venues:
                if (
                    not isinstance(venue_entry, list)
                    or len(venue_entry) != 2
                    or not isinstance(venue_entry[1], dict)
                ):
                    continue

                venue_name = venue_entry[0]
                details = venue_entry[1]

                funding_rate_str = details.get("fundingRate")
                next_funding_time_ms = details.get("nextFundingTime")

                if funding_rate_str is None or next_funding_time_ms is None:
                    continue

                try:
                    funding_rate = float(funding_rate_str)
                    next_time = pd.to_datetime(
                        int(next_funding_time_ms), unit="ms", utc=True
                    )
                except (ValueError, TypeError):
                    continue

                rows.append(
                    {
                        "asset": asset,
                        "venue": venue_name,
                        "funding_rate": funding_rate,
                        "funding_rate_bps": funding_rate * 10000.0,
                        "next_funding_time": next_time,
                    }
                )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "asset",
                    "venue",
                    "funding_rate",
                    "funding_rate_bps",
                    "next_funding_time",
                ]
            )

        df = pd.DataFrame(rows)
        df = df.sort_values(["asset", "venue"]).reset_index(drop=True)
        return df

    def get_funding_history(
        self,
        coin: str,
        start_time_ms: int,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical funding rates for a single coin on Hyperliquid.

        Parameters
        ----------
        coin : str
            Coin symbol, for example "BTC" or "ETH".
        start_time_ms : int
        end_time_ms : Optional[int]

        Returns
        -------
        pd.DataFrame
            Columns:
            - coin
            - time
            - funding_rate
            - funding_rate_bps
            - premium
            - premium_bps
        """
        if start_time_ms < 0:
            raise ValueError("start_time_ms must be non-negative")

        if end_time_ms is not None and start_time_ms > end_time_ms:
            raise ValueError("start_time_ms must be <= end_time_ms")

        payload: Dict[str, Any] = {
            "type": "fundingHistory",
            "coin": coin,
            "startTime": int(start_time_ms),
        }
        if end_time_ms is not None:
            payload["endTime"] = int(end_time_ms)

        data = self._post("/info", payload)

        if not isinstance(data, list) or not data:
            return pd.DataFrame(
                columns=[
                    "coin",
                    "time",
                    "funding_rate",
                    "funding_rate_bps",
                    "premium",
                    "premium_bps",
                ]
            )

        df = pd.DataFrame(data)

        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        df["funding_rate"] = df["fundingRate"].astype(float)
        df["premium"] = df["premium"].astype(float)

        df["funding_rate_bps"] = df["funding_rate"] * 10000.0
        df["premium_bps"] = df["premium"] * 10000.0

        df = df[
            [
                "coin",
                "time",
                "funding_rate",
                "funding_rate_bps",
                "premium",
                "premium_bps",
            ]
        ].sort_values("time")

        df.reset_index(drop=True, inplace=True)
        return df

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Any:
        resp = self.client.post(endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()


class HyperliquidClient(HyperliquidInfoClient):
    """
    Thin adapter to match the dashboard API:

    get_funding_history(
        coin: str,
        start_time: datetime,
        end_time: Optional[datetime],
    )
    """

    @staticmethod
    def _to_millis(dt: datetime) -> int:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    def get_funding_history(
        self,
        coin: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        start_ms = self._to_millis(start_time)
        end_ms = self._to_millis(end_time) if end_time is not None else None

        return super().get_funding_history(
            coin=coin,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
        )
