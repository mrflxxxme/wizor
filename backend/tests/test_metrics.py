"""Unit: /metrics отдаёт Prometheus-экспозицию (observability-поверхность).

/metrics смонтирован как sub-app, поэтому bare-путь редиректит на /metrics/ (307);
тест следует редиректу и проверяет, что экспозиция доступна и не пуста.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_exposition(app_client: AsyncClient) -> None:
    resp = await app_client.get("/metrics", follow_redirects=True)
    assert resp.status_code == 200
    # Prometheus text-экспозиция содержит HELP/TYPE-комментарии.
    assert "# HELP" in resp.text or "# TYPE" in resp.text
