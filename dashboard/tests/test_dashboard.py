"""Dashboard integration checks for the fixed synthetic demo dataset."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class DashboardTests(unittest.TestCase):
    def assert_loaded(self, app):
        self.assertEqual(
            len(app.exception),
            0,
            [element.value for element in app.exception],
        )
        self.assertEqual(
            len(app.error),
            0,
            [element.value for element in app.error],
        )

    def open_app(self):
        app = AppTest.from_file(
            str(APP_PATH),
            default_timeout=30,
        ).run()

        self.assert_loaded(app)
        return app

    def metrics(self, app):
        return {
            metric.label: metric.value
            for metric in app.metric
        }

    def select_snapshot(self, app, label):
        selector = app.selectbox[0]
        index = list(selector.options).index(label)
        selector.select_index(index).run()
        self.assert_loaded(app)

    def test_latest_revenue(self):
        app = self.open_app()

        self.assertEqual(
            self.metrics(app),
            {
                "MRR (USD)": "56,400",
                "Active accounts": "216",
                "New MRR (USD)": "1,400",
                "Churned MRR (USD)": "900",
            },
        )

        self.assertEqual(app.metric[0].delta, "+500")

    def test_july_revenue_and_refresh(self):
        app = self.open_app()
        self.select_snapshot(app, "July 01, 2026")

        expected = {
            "MRR (USD)": "48,500",
            "Active accounts": "195",
            "New MRR (USD)": "900",
            "Churned MRR (USD)": "1,100",
        }

        self.assertEqual(self.metrics(app), expected)
        self.assertEqual(app.metric[0].delta, "-200")

        app.sidebar.button[0].click().run()
        self.assert_loaded(app)

        self.assertEqual(
            app.selectbox[0].value.strftime("%Y-%m-%d"),
            "2026-07-01",
        )
        self.assertEqual(self.metrics(app), expected)

    def test_first_snapshot_has_no_movements(self):
        app = self.open_app()
        self.select_snapshot(app, "January 01, 2025")

        self.assertEqual(
            self.metrics(app),
            {
                "MRR (USD)": "0",
                "Active accounts": "0",
                "New MRR (USD)": "—",
                "Churned MRR (USD)": "—",
            },
        )

        messages = [element.value for element in app.info]

        self.assertTrue(
            any(
                "no preceding checkpoint" in message
                for message in messages
            )
        )
        self.assertTrue(
            any(
                "No movement periods" in message
                for message in messages
            )
        )

    def test_retention_page(self):
        app = self.open_app()
        app.switch_page("pages/02_Retention.py").run()
        self.assert_loaded(app)

        self.assertEqual(
            self.metrics(app),
            {
                "Subscription start cohorts": "21",
                "Observed cohort checkpoints": "231",
                "Subscriptions in observed cohorts": "250",
            },
        )

        tables = [
            element.value
            for element in app.dataframe
            if "Pooled monthly churn (%)" in element.value.columns
        ]

        self.assertEqual(len(tables), 1)

        churn = tables[0].set_index("Plan")[
            "Pooled monthly churn (%)"
        ].to_dict()

        self.assertEqual(
            churn,
            {
                "Growth": 1.78,
                "Starter": 1.61,
                "Enterprise": 1.08,
            },
        )

    def test_collections_page(self):
        app = self.open_app()
        app.switch_page("pages/03_Collections.py").run()
        self.assert_loaded(app)

        self.assertEqual(
            self.metrics(app),
            {
                "Outstanding balance (USD)": "97,920",
                "Overdue balance (USD)": "89,620",
                "91+ days overdue (USD)": "64,700",
                "Overdue invoices": "291",
            },
        )

        activity_tables = [
            element.value
            for element in app.dataframe
            if "Payment activity" in element.value.columns
        ]

        self.assertEqual(len(activity_tables), 1)

        activity = activity_tables[0].set_index("Payment activity")

        self.assertEqual(
            activity["Overdue invoices"].to_dict(),
            {
                "Failed attempts only": 142,
                "No completed attempts": 88,
                "Partially paid": 61,
            },
        )

        self.assertEqual(
            activity["Overdue balance (USD)"].to_dict(),
            {
                "Failed attempts only": 41400.0,
                "No completed attempts": 34900.0,
                "Partially paid": 13320.0,
            },
        )

        priority_tables = [
            element.value
            for element in app.dataframe
            if "Account ID" in element.value.columns
            and len(element.value) == 10
        ]

        self.assertEqual(len(priority_tables), 1)

        self.assertAlmostEqual(
            float(priority_tables[0]["Overdue (USD)"].sum()),
            31200.0,
            places=2,
        )


if __name__ == "__main__":
    unittest.main()