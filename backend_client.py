# backend_client.py
from __future__ import annotations

from dataclasses import dataclass
import requests


@dataclass(frozen=True)
class BackendClient:
    # Simple HTTP client for Flask backend.

    base_url: str

    def upload_image(self, image_bytes: bytes, filename: str | None = None) -> str:
        files = {"file": (filename or "map.png", image_bytes, "application/octet-stream")}
        r = requests.post(f"{self.base_url}/uploadImage", files=files, timeout=60)
        r.raise_for_status()

        data = r.json()
        if data.get("status") != "success" or not data.get("image_id"):
            raise RuntimeError(f"Upload failed: {data}")

        return data["image_id"]

    def analyze(
        self,
        image_id: str,
        audience: str,
        purpose: str,
        distribution: str = "unknown",
    ) -> dict:
        url = f"{self.base_url}/analyze"
        payload = {
            "image_id": image_id,
            "audience": audience,
            "purpose": purpose,
            "distribution": distribution,
        }

        try:
            r = requests.post(url, json=payload, timeout=(10, 300))
        except requests.RequestException as e:
            raise RuntimeError(f"Request error calling {url}: {e}") from e

        try:
            j = r.json()
        except Exception as e:
            raise RuntimeError(f"Response not JSON: {e}\n\nBody (first 2000):\n{r.text[:2000]}")

        if not r.ok:
            msg = j.get("error") if isinstance(j, dict) else str(j)
            raise RuntimeError(f"Backend HTTP {r.status_code}: {msg}")

        if not (isinstance(j, dict) and j.get("status") == "success"):
            raise RuntimeError(f"Backend non-success JSON: {j}")

        return j