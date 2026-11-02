"""Check funnel metrics, channel filtering, and refresh behavior."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


DASHBOARD_DIR = Path(__file__).resolve().parents[1]


class FunnelDashboardTests(unittest.TestCase):
    def assert_loaded(self, app):
        self.assertEqual(
            len(app.exception),
            0,
            str(app.exception),
        )
        self.assertEqual(
            len(app.error),
            0,
            str(app.error),
        )

    def open_funnel(self):
        app = AppTest.from_file(
            str(DASHBOARD_DIR / "app.py"),
            default_timeout=30,
        ).run()

        self.assert_loaded(app)

        app.switch_page("pages/04_Funnel.py").run()
        self.assert_loaded(app)

        return app

    def metrics(self, app):
        return {
            metric.label: metric.value
            for metric in app.metric
        }

    def channel_table(self, app):
        tables = [
            element.value
            for element in app.dataframe
            if "Acquisition channel" in element.value.columns
        ]

        self.assertEqual(len(tables), 1)
        return tables[0]

    def test_all_channels_funnel(self):
        app = self.open_funnel()

        self.assertEqual(
            self.metrics(app),
            {
                "Eligible prospects": "984",
                "Trial starts": "590",
                "Subscription starts": "250",
                "First payments": "217",
                "Prospect to trial": "59.96%",
                "Trial to subscription": "42.37%",
                "Subscription to payment": "86.80%",
                "Prospect to payment": "22.05%",
            },
        )

        table = self.channel_table(app)

        self.assertEqual(len(table), 5)
        self.assertEqual(int(table["Observed prospects"].sum()), 1000)
        self.assertEqual(int(table["Pending prospects"].sum()), 16)

    def test_direct_channel_and_refresh(self):
        app = self.open_funnel()

        app.sidebar.selectbox[0].select("Direct").run()
        self.assert_loaded(app)

        expected = {
            "Eligible prospects": "183",
            "Trial starts": "114",
            "Subscription starts": "53",
            "First payments": "48",
            "Prospect to trial": "62.30%",
            "Trial to subscription": "46.49%",
            "Subscription to payment": "90.57%",
            "Prospect to payment": "26.23%",
        }

        self.assertEqual(self.metrics(app), expected)

        app.sidebar.button[0].click().run()
        self.assert_loaded(app)

        self.assertEqual(
            app.sidebar.selectbox[0].value,
            "Direct",
        )
        self.assertEqual(self.metrics(app), expected)

        table = self.channel_table(app)

        self.assertEqual(len(table), 1)
        self.assertEqual(
            table.iloc[0]["Acquisition channel"],
            "Direct",
        )
        self.assertEqual(
            int(table.iloc[0]["Pending prospects"]),
            3,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)