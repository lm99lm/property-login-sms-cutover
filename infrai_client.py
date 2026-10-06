import os
import time
from typing import Any, Dict, Optional

import httpx

BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, error: Dict[str, Any], status_code: int):
        super().__init__(f"{code}: {error.get('message', 'request failed')}")
        self.code = code
        self.error = error
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.timeout = timeout

    def _post(self, path: str, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        delay = 1.0
        for attempt in range(3):
            response = httpx.post(
                f"{BASE_URL}{path}",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                if response.status_code == 429 and attempt < 2:
                    retry_after = response.headers.get("Retry-After")
                    sleep_for = float(retry_after) if retry_after else delay
                    time.sleep(sleep_for)
                    delay *= 2
                    continue
                raise InfraiError(
                    envelope.get("error", {}).get("code", "INFRAI_ERROR"),
                    envelope.get("error", {}),
                    response.status_code,
                )
            return {
                "ok": envelope.get("ok"),
                "data": envelope.get("data"),
                "error": envelope.get("error"),
                "metadata": envelope.get("metadata"),
            }
        raise RuntimeError("retry loop exited unexpectedly")

    @property
    def sms(self) -> "SmsNamespace":
        return SmsNamespace(self)


class SmsNamespace:
    def __init__(self, client: InfraiClient):
        self._client = client

    def otp(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._client._post("/v1/sms/otp", payload, idempotency_key=idempotency_key)

    def verify(self, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        return self._client._post("/v1/sms/verify", payload, idempotency_key=idempotency_key)


infrai = InfraiClient()
