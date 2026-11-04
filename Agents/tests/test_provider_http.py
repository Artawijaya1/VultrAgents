import unittest
import httpx
from agent_core.provider_http import HTTPProcurementProvider, BackendProviderError


class HTTPProviderTest(unittest.TestCase):
    def setUp(self):
        def handler(request):
            if request.headers.get('Authorization') != 'Bearer test-token':
                return httpx.Response(401)
            if request.url.path.endswith('/invoices'):
                return httpx.Response(200, json={'items': [{'record_id': 'R1', 'supplier_id': 'S1'}]})
            if request.url.path.endswith('/pos/PO-404'):
                return httpx.Response(404)
            return httpx.Response(200, json={'po_id': 'PO-1', 'supplier_id': 'S1'})
        self.http = httpx.Client(transport=httpx.MockTransport(handler))
        self.provider = HTTPProcurementProvider('http://127.0.0.1:3000', 'test-token', client=self.http)

    def tearDown(self):
        self.http.close()

    def test_invoice_contract(self):
        self.assertEqual(len(self.provider.get_invoices('S1')), 1)

    def test_po_not_found(self):
        self.assertIsNone(self.provider.get_po('PO-404'))

    def test_http_security(self):
        with self.assertRaises(ValueError):
            HTTPProcurementProvider('http://example.com', 'test-token')

    def test_requires_service_token(self):
        with self.assertRaises(ValueError):
            HTTPProcurementProvider('http://127.0.0.1:3000', '')


if __name__ == '__main__':
    unittest.main()
