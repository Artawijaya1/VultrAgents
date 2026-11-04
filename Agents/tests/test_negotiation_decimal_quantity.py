"""Regression tests for Backend PostgreSQL NUMERIC(18,4) quantity."""
import unittest
from agent_core.data_provider import MockProvider
from agent_core.negotiation import recommend_negotiation


class DecimalQuantityTests(unittest.TestCase):
    def setUp(self):
        self.provider = MockProvider()

    def check_quantity(self, value):
        self.provider.pos['PO-001']['quantity'] = value
        return recommend_negotiation(self.provider, 'PO-001')

    def test_integer_quantity_keeps_previous_behavior(self):
        result = self.check_quantity(10)
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['quantity'], 10)
        self.assertTrue(result['requires_approval'])

    def test_decimal_string_from_postgres_is_accepted(self):
        result = self.check_quantity('10.0000')
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['quantity'], 10)
        self.assertTrue(result['requires_approval'])
        self.assertEqual(result['potential_savings_vs_offer'],
                         (result['offered_unit_price'] - result['opening_offer_unit']) * 10)

    def test_fractional_quantity_must_not_be_truncated(self):
        self.assertEqual(self.check_quantity('10.5000')['status'], 'invalid_data')

    def test_bad_quantities_are_rejected_without_exception(self):
        for value in ('abc', 'NaN', 'Infinity', '0.0000', '-1.0000', None, '1e1000000'):
            with self.subTest(value=value):
                self.assertEqual(self.check_quantity(value)['status'], 'invalid_data')


if __name__ == '__main__':
    unittest.main()
