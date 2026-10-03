from __future__ import annotations

import unittest

from omr_notifications.models import EventNormalizer
from omr_notifications.policy import PolicyEngine, condition_matches


def policy(identifier, priority=0, controls=None, terminal=False, conditions=None):
    return {
        "id": identifier,
        "enabled": True,
        "priority": priority,
        "trigger": {"types": ["test.event"]},
        "conditions": conditions or [],
        "controls": controls or {},
        "actions": [{"type": "event.record", "config": {}}],
        "terminal": terminal,
        "errorStrategy": "continue",
    }


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.event = EventNormalizer().create(
            event_type="test.event", listener_id="input", adapter="fixture",
            data={"name": "Report.pdf", "count": 3, "tags": ["work"]},
        )

    def test_priority_then_id_order_and_terminal(self):
        engine = PolicyEngine([policy("z", 10), policy("b", 20, terminal=True), policy("a", 20)])
        self.assertEqual(["a", "b"], [x.policy["id"] for x in engine.evaluate(self.event, now=100)])

    def test_typed_conditions(self):
        self.assertTrue(condition_matches(self.event, {"field": "data.name", "operator": "suffix", "value": ".pdf"}))
        self.assertTrue(condition_matches(self.event, {"field": "data.count", "operator": "gte", "value": 3}))
        self.assertFalse(condition_matches(self.event, {"field": "data.missing", "operator": "exists", "value": True}))

    def test_cooldown_and_rate_limit(self):
        engine = PolicyEngine([policy("limited", controls={
            "cooldownSeconds": 5,
            "rateLimit": {"count": 2, "windowSeconds": 30},
        })])
        first = engine.evaluate(self.event, now=100)[0]
        engine.mark_executed(first, now=100)
        self.assertEqual("cooldown", engine.evaluate(self.event, now=102)[0].reason)
        second = engine.evaluate(self.event, now=106)[0]
        engine.mark_executed(second, now=106)
        self.assertEqual("rate-limit", engine.evaluate(self.event, now=112)[0].reason)
        self.assertEqual("matched", engine.evaluate(self.event, now=131)[0].status)

    def test_debounce_keeps_newest_event(self):
        engine = PolicyEngine([policy("quiet", controls={"debounceSeconds": 5, "groupBy": ["listenerId"]})])
        first = engine.evaluate(self.event, now=10)[0]
        replacement = EventNormalizer(initial_sequence=1).create(event_type="test.event", listener_id="input", adapter="fixture", data={"name": "new"})
        engine.evaluate(replacement, now=12)
        self.assertEqual("deferred", first.status)
        self.assertEqual([], engine.flush_debounced(now=16))
        flushed = engine.flush_debounced(now=17)
        self.assertEqual(replacement.id, flushed[0].event.id)

    def test_causal_depth_suppresses_side_effects(self):
        event = EventNormalizer(max_depth=8).create(event_type="test.event", listener_id="input", adapter="fixture", causal_depth=8)
        result = PolicyEngine([policy("loop")], max_depth=8).evaluate(event)
        self.assertEqual("causal-depth", result[0].reason)

    def test_self_origin_is_filtered_by_default(self):
        event = EventNormalizer().create(event_type="test.event", listener_id="input", adapter="fixture", origin="omr.action.exec")
        self.assertEqual([], PolicyEngine([policy("loop")]).evaluate(event))


if __name__ == "__main__":
    unittest.main()
