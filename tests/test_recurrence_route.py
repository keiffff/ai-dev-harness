import unittest
from dataclasses import replace

from codex.recurrence_route import Route, State, select_route


class RecurrenceRouteTests(unittest.TestCase):
    def setUp(self):
        self.prior = Route("render", "document", "local", State.READY, "completed artifact")
        self.new = Route("alternate-render", "document", "local", State.READY)
        self.blocked = Route("service-render", "document", "service", State.BLOCKED)

    def test_repeat_resumes_the_previously_completed_route(self):
        other_contract = replace(self.prior, contract="outline")
        decision = select_route("document", [self.new, other_contract, self.prior],
                                {"local"}, repeat=True)
        self.assertEqual((decision.action, decision.options), ("resume", (self.prior,)))

    def test_history_does_not_grant_capability(self):
        decision = select_route("document", [self.prior, self.blocked],
                                {"service"}, repeat=True)
        self.assertEqual(decision.action, "unresolved")

    def test_explicit_operation_controls_selection(self):
        routes = [self.prior, self.new, self.blocked]
        decision = select_route("document", routes, {"local", "service"}, repeat=True,
                                explicit=self.new.operation)
        self.assertEqual(decision.options, (self.new,))
        decision = select_route("document", routes, {"local", "service"}, repeat=True,
                                explicit=self.blocked.operation)
        self.assertEqual(decision.action, "unresolved")

    def test_recoverable_input_is_returned_to_the_caller(self):
        prior = replace(self.prior, state=State.RECOVERABLE_INPUT, missing_input="source")
        decision = select_route("document", [self.new, prior], {"local"}, repeat=True)
        self.assertEqual((decision.action, decision.options), ("collect_input", (prior,)))

    def test_unbound_and_ambiguous_work_are_left_to_the_caller(self):
        self.assertEqual(select_route(None, [self.prior], {"local"}).action, "fall_through")
        decision = select_route("document", [self.prior, self.new], {"local"})
        self.assertEqual(decision.action, "compare_routes")


if __name__ == "__main__":
    unittest.main()
