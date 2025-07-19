import gc
import unittest

from automojo.networking import trafficcapturecontext


class DummyOwner:
    pass


def dummy_destroy(context):
    dummy_destroy.called_with = context

dummy_destroy.called_with = None


class TrafficCaptureContextTests(unittest.TestCase):

    def test_init_noncallable_destroy_method_raises_value_error(self):
        with self.assertRaises(ValueError):
            trafficcapturecontext.TrafficCaptureContext(DummyOwner(), "sid", "1.1.1.1", None)

    def test_enter_returns_self(self):
        ctx = trafficcapturecontext.TrafficCaptureContext(DummyOwner(), "sid", "1.1.1.1", dummy_destroy)
        with ctx as captured:
            self.assertIs(captured, ctx)
        # ensure destroy not called until exit
        self.assertIs(dummy_destroy.called_with, ctx)

    def test_exit_calls_destroy_and_returns_false(self):
        ctx = trafficcapturecontext.TrafficCaptureContext(DummyOwner(), "sid", "1.1.1.1", dummy_destroy)
        result = ctx.__exit__(None, None, None)
        self.assertFalse(result)
        self.assertIs(dummy_destroy.called_with, ctx)

    def test_append_capture_and_captures_property(self):
        ctx = trafficcapturecontext.TrafficCaptureContext(DummyOwner(), "sid", "1.1.1.1", dummy_destroy)
        headers = {"a": "b"}
        body = "test"
        ctx.append_capture(headers, body)
        captures = ctx.captures
        self.assertEqual(len(captures), 1)
        self.assertEqual(captures[0], (headers, body))
        # modifying returned list should not affect internal state
        captures.append((None, None))
        self.assertEqual(len(ctx.captures), 1)

    def test_owner_returns_none_after_owner_deleted(self):
        owner = DummyOwner()
        ctx = trafficcapturecontext.TrafficCaptureContext(owner, "sid", "1.1.1.1", dummy_destroy)
        self.assertIs(ctx.owner, owner)
        del owner
        gc.collect()
        self.assertIsNone(ctx.owner)

    def test_properties_return_expected_values(self):
        ctx = trafficcapturecontext.TrafficCaptureContext(DummyOwner(), "identifier", "2.2.2.2", dummy_destroy)
        self.assertEqual(ctx.identifier, "identifier")
        self.assertEqual(ctx.fromip, "2.2.2.2")


if __name__ == "__main__":
    unittest.main()
