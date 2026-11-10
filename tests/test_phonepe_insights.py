import sqlite3
import unittest
from phonepe_insights import get_period_insights


class SelectedQuarterTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('CREATE TABLE aggregated_transaction (year INTEGER, quarter TEXT, level TEXT, state TEXT, txn_type TEXT, count INTEGER, amount REAL)')
        self.conn.executemany('INSERT INTO aggregated_transaction VALUES (?, ?, ?, ?, ?, ?, ?)', [
            (2023, '4', 'state', 'A', 'Merchant', 100, 1000),
            (2024, '4', 'state', 'A', 'Merchant', 200, 1500),
            (2024, '4', 'state', 'B', 'Peer', 100, 2500),
            (2024, '4', 'country', None, 'Peer', 300, 4000),
            (2024, '3', 'state', 'A', 'Merchant', 999, 9999),
        ])

    def test_state_only_selected_period_and_year_on_year(self):
        result = get_period_insights(self.conn, 2024, 4)
        self.assertEqual(result['total_count'], 300)
        self.assertEqual(result['total_amount'], 4000)
        self.assertAlmostEqual(result['count_growth'], 200)
        self.assertAlmostEqual(result['amount_growth'], 300)
        self.assertEqual(result['categories'].index[0], 'Peer')
        self.assertEqual(result['states'].index[0], 'B')
        self.assertEqual(result['top_five_share'], 100)

    def test_missing_period_and_previous_year(self):
        self.assertIsNone(get_period_insights(self.conn, 2022, 1))
        self.assertIsNone(get_period_insights(self.conn, 2023, 4)['count_growth'])

    def tearDown(self): self.conn.close()


if __name__ == '__main__': unittest.main()
