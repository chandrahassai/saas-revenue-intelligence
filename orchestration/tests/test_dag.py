"""Validate DAG loading, task dependencies, and failure propagation."""

import unittest

from airflow.dag_processing.dagbag import DagBag


DAG_ID = "saas_analytics_workflow"

EXPECTED_DEPENDENCIES = {
    "build_and_test_dbt": {"test_dashboard_pages"},
    "test_dashboard_pages": {"generate_dbt_documentation"},
    "generate_dbt_documentation": set(),
}


class AirflowDagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dagbag = DagBag()

    def get_workflow(self):
        dag = self.dagbag.dags.get(DAG_ID)
        self.assertIsNotNone(
            dag,
            f"{DAG_ID} was not loaded. "
            f"Import errors: {self.dagbag.import_errors}",
        )
        return dag

    def test_dag_loads_without_errors(self):
        self.assertEqual(
            self.dagbag.import_errors,
            {},
            f"DAG import errors: {self.dagbag.import_errors}",
        )
        self.assertEqual(set(self.dagbag.dags), {DAG_ID})

    def test_task_dependencies(self):
        dag = self.get_workflow()

        actual_dependencies = {
            task.task_id: set(task.downstream_task_ids)
            for task in dag.tasks
        }

        self.assertEqual(
            actual_dependencies,
            EXPECTED_DEPENDENCIES,
        )

    def test_tasks_require_success_and_fail_on_nonzero_exit(self):
        dag = self.get_workflow()

        for task in dag.tasks:
            with self.subTest(task_id=task.task_id):
                self.assertEqual(task.trigger_rule, "all_success")

                # BashOperator normalizes skip_on_exit_code=None
                # to an empty list: no exit codes cause skipping.
                self.assertEqual(task.skip_on_exit_code, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)