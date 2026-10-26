import unittest

from scripts.reconcile_build import decide_build, run_title


class ReconcileBuildTests(unittest.TestCase):
    def setUp(self):
        self.version = "9.7.0"
        self.commit = "a" * 40
        self.title = run_title(self.version, self.commit)

    def test_dispatches_when_current_lock_has_no_run_or_release(self):
        self.assertEqual(decide_build(self.version, self.commit, [], False), "dispatch")

    def test_does_not_duplicate_queued_or_running_build(self):
        runs = [{"displayTitle": self.title, "status": "in_progress", "conclusion": None, "createdAt": "2026-01-02T00:00:00Z"}]
        self.assertEqual(decide_build(self.version, self.commit, runs, False), "active")

    def test_any_matching_active_run_blocks_dispatch(self):
        runs = [
            {"displayTitle": self.title, "status": "in_progress", "conclusion": None, "createdAt": "2026-01-01T00:00:00Z"},
            {"displayTitle": self.title, "status": "completed", "conclusion": "failure", "createdAt": "2026-01-02T00:00:00Z"},
        ]
        self.assertEqual(decide_build(self.version, self.commit, runs, False), "active")

    def test_successful_run_and_release_are_complete(self):
        runs = [{"displayTitle": self.title, "status": "completed", "conclusion": "success", "createdAt": "2026-01-02T00:00:00Z"}]
        self.assertEqual(decide_build(self.version, self.commit, runs, True), "complete")

    def test_existing_release_is_migration_baseline_without_new_format_run(self):
        self.assertEqual(decide_build(self.version, self.commit, [], True), "complete")

    def test_failed_matching_run_retries_even_if_release_exists(self):
        runs = [{"displayTitle": self.title, "status": "completed", "conclusion": "failure", "createdAt": "2026-01-02T00:00:00Z"}]
        self.assertEqual(decide_build(self.version, self.commit, runs, True), "dispatch")

    def test_unrelated_run_title_does_not_consume_retry_budget(self):
        runs = [{"displayTitle": "Build WUD 9.6.0 (old)", "status": "completed", "conclusion": "failure", "createdAt": "2026-01-02T00:00:00Z"}]
        self.assertEqual(decide_build(self.version, self.commit, runs, False), "dispatch")

    def test_caps_automatic_attempts(self):
        runs = [
            {"displayTitle": self.title, "status": "completed", "conclusion": "failure", "createdAt": f"2026-01-0{i}T00:00:00Z"}
            for i in range(1, 4)
        ]
        self.assertEqual(decide_build(self.version, self.commit, runs, True), "capped")

    def test_successful_latest_attempt_wins_after_retries(self):
        runs = [
            {"displayTitle": self.title, "status": "completed", "conclusion": "failure", "createdAt": "2026-01-01T00:00:00Z"},
            {"displayTitle": self.title, "status": "completed", "conclusion": "success", "createdAt": "2026-01-03T00:00:00Z"},
            {"displayTitle": self.title, "status": "completed", "conclusion": "failure", "createdAt": "2026-01-02T00:00:00Z"},
        ]
        self.assertEqual(decide_build(self.version, self.commit, runs, True), "complete")

    def test_unknown_release_api_state_fails_closed(self):
        self.assertEqual(decide_build(self.version, self.commit, [], None), "ambiguous")

    def test_unknown_matching_run_state_fails_closed(self):
        runs = [{"displayTitle": self.title, "status": "mystery", "conclusion": "failure", "createdAt": "2026-01-02T00:00:00Z"}]
        self.assertEqual(decide_build(self.version, self.commit, runs, False), "ambiguous")


if __name__ == "__main__":
    unittest.main()
