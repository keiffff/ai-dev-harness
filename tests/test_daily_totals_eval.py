import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('daily_totals_eval', ROOT / 'evals/task-continuity/daily_totals.py')
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)


class DailyTotalsAcceptanceTests(unittest.TestCase):
    def test_unfinished_cli_fails_despite_working_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / 'task'
            daily.seed(task)
            checks = daily.check(task)
            self.assertTrue(all(c['helper_exit'] == 0 for c in checks))
            self.assertFalse(all(c['pass'] for c in checks))

    def test_data_driven_cli_passes_all_frozen_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory) / 'task'
            daily.seed(task)
            entry = task / 'report.py'
            entry.write_text(entry.read_text().replace("summarize(args.input, 'UTC')", "summarize(args.input, args.timezone)"))
            self.assertTrue(all(c['pass'] for c in daily.check(task)))

    def test_fixture_specific_output_and_failed_generation_are_rejected(self):
        for broken in (False, True):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as directory:
                task = Path(directory) / 'task'
                daily.seed(task)
                code = "import argparse\nfrom pathlib import Path\np=argparse.ArgumentParser()\np.add_argument('--input')\np.add_argument('--output')\np.add_argument('--timezone')\na=p.parse_args()\n"
                code += "raise SystemExit(1)\n" if broken else "Path(a.output).write_text('day,units\\n2026-01-04,2\\n2026-01-05,8\\n')\n"
                (task / 'report.py').write_text(code)
                self.assertFalse(all(c['pass'] for c in daily.check(task)))


if __name__ == '__main__':
    unittest.main()
