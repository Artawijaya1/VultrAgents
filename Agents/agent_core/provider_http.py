"""Read-only adapter contract with teammate's backend. Never passes arbitrary SQL."""
from __future__ import annotations
import os
from urllib.parse import urlsplit

import httpx

from .data_provider import MockProvider


class BackendProviderError(RuntimeError):
    pass


class HTTPProcurementProvider:
    """Expected backend routes are documented in docs/INTEGRATION_CONTRACT.md."""
    def __init__(self, base_url: str, service_token: str, client: httpx.Client | None = None):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError('PROCUREMENT_BACKEND_URL harus URL http(s) yang valid')
        if parsed.scheme == 'http' and parsed.hostname not in {'localhost', '127.0.0.1', '::1'}:
            raise ValueError('Koneksi non-local harus HTTPS')
        if not service_token:
            raise ValueError('PROCUREMENT_SERVICE_TOKEN wajib pada mode http')
        self.base_url = base_url.rstrip('/')
        self.token = service_token
        self.client = client or httpx.Client(timeout=5.0, follow_redirects=False)

    def _get(self, path: str):
        try:
            res = self.client.get(self.base_url + path,
                                  headers={'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'})
            if res.status_code == 404:
                return None
            res.raise_for_status()
            return res.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise BackendProviderError('Backend procurement tidak tersedia atau respons tidak valid') from exc

    def get_po(self, po_id: str) -> dict | None:
        data = self._get('/api/v1/procurement/pos/' + po_id)
        if data is not None and not isinstance(data, dict):
            raise BackendProviderError('PO response harus JSON object')
        return data

    def get_supplier(self, supplier_id: str) -> dict | None:
        data = self._get('/api/v1/procurement/suppliers/' + supplier_id)
        if data is not None and not isinstance(data, dict):
            raise BackendProviderError('Supplier response harus JSON object')
        return data

    def get_invoices(self, supplier_id: str) -> list[dict]:
        data = self._get('/api/v1/procurement/suppliers/' + supplier_id + '/invoices')
        if data is None:
            return []
        if isinstance(data, dict) and isinstance(data.get('items'), list):
            data = data['items']
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise BackendProviderError('Invoice response harus array atau {"items": [...]}')
        return data


def build_provider():
    mode = os.getenv('AGENT_DATA_MODE', 'mock').lower()
    if mode == 'mock':
        return MockProvider()
    if mode == 'http':
        return HTTPProcurementProvider(
            os.getenv('PROCUREMENT_BACKEND_URL', ''),
            os.getenv('PROCUREMENT_SERVICE_TOKEN', ''),
        )
    raise ValueError('AGENT_DATA_MODE hanya mock atau http')
