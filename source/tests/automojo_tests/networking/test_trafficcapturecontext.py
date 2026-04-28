"""
    .. module:: test_trafficcapturecontext
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`automojo.networking.trafficcapturecontext` module.

    .. moduleauthor:: Automojo Test Author
"""

import gc
import unittest

from automojo.networking import trafficcapturecontext


class DummyOwner:
    """
        Plain owner object used by tests to verify weak-reference behavior.
    """

    def __init__(self) -> None:
        """
            Initialize a :class:`DummyOwner`.
        """
        return


class _DestroyRecorder:
    """
        Callable container that records the most recent context passed to it.
    """

    def __init__(self) -> None:
        """
            Initialize a :class:`_DestroyRecorder`.
        """
        self.called_with = None
        self.call_count = 0
        return

    def __call__(self, context: object) -> None:
        """
            Record an invocation.

            :param context: The capture context being destroyed.

            :returns: ``None``
        """
        self.called_with = context
        self.call_count += 1
        return


class InitializerTests(unittest.TestCase):
    """
        Tests for :class:`TrafficCaptureContext.__init__`.
    """

    def test_noncallable_destroy_method_raises_value_error(self) -> None:
        """
            Verify a ``None`` destroy method raises ``ValueError``.
        """
        owner = DummyOwner()
        with self.assertRaises(ValueError):
            trafficcapturecontext.TrafficCaptureContext(
                owner, "sid", "1.1.1.1", None
            )
        return

    def test_non_callable_destroy_method_raises_value_error(self) -> None:
        """
            Verify a non-callable destroy method raises ``ValueError``.
        """
        owner = DummyOwner()
        with self.assertRaises(ValueError):
            trafficcapturecontext.TrafficCaptureContext(
                owner, "sid", "1.1.1.1", "not-callable"
            )
        return


class ContextManagerTests(unittest.TestCase):
    """
        Tests for the context-manager protocol of :class:`TrafficCaptureContext`.
    """

    def test_enter_returns_self(self) -> None:
        """
            Verify ``__enter__`` returns the context instance.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        with ctx as captured:
            self.assertIs(captured, ctx)
            self.assertEqual(recorder.call_count, 0)
        self.assertIs(recorder.called_with, ctx)
        self.assertEqual(recorder.call_count, 1)
        return

    def test_exit_calls_destroy_method_on_normal_exit(self) -> None:
        """
            Verify the destroy method runs when the with-block exits cleanly.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        rtnval = ctx.__exit__(None, None, None)
        self.assertFalse(rtnval)
        self.assertIs(recorder.called_with, ctx)
        return

    def test_exit_calls_destroy_method_on_exception_path(self) -> None:
        """
            Verify the destroy method runs even when the body raised, and the
            exception is re-raised (``__exit__`` returns ``False``).
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )

        raised = False
        try:
            with ctx:
                raise RuntimeError("boom")
        except RuntimeError:
            raised = True

        self.assertTrue(raised)
        self.assertEqual(recorder.call_count, 1)
        self.assertIs(recorder.called_with, ctx)
        return


class CaptureStorageTests(unittest.TestCase):
    """
        Tests for the captured-data accessor and append helper.
    """

    def test_captures_starts_empty(self) -> None:
        """
            Verify the captures list is empty on construction.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        rtnval = ctx.captures
        self.assertEqual(rtnval, [])
        return

    def test_append_capture_records_tuple(self) -> None:
        """
            Verify ``append_capture`` stores a (headers, body) tuple.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        headers = {"a": "b"}
        body = "test"
        ctx.append_capture(headers, body)
        captures = ctx.captures
        self.assertEqual(len(captures), 1)
        self.assertEqual(captures[0], (headers, body))
        return

    def test_captures_property_returns_a_copy(self) -> None:
        """
            Verify mutating the returned capture list does not affect the
            internal storage.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        ctx.append_capture({"a": "b"}, "body")
        captures = ctx.captures
        captures.append((None, None))
        self.assertEqual(len(ctx.captures), 1)
        return

    def test_append_capture_returns_none(self) -> None:
        """
            Verify ``append_capture`` returns ``None``.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        rtnval = ctx.append_capture({}, "")
        self.assertIsNone(rtnval)
        return


class PropertyTests(unittest.TestCase):
    """
        Tests for the simple data accessor properties.
    """

    def test_identifier_returns_supplied_value(self) -> None:
        """
            Verify the ``identifier`` property echoes the constructor argument.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "identifier", "2.2.2.2", recorder
        )
        self.assertEqual(ctx.identifier, "identifier")
        return

    def test_fromip_returns_supplied_value(self) -> None:
        """
            Verify the ``fromip`` property echoes the constructor argument.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "identifier", "2.2.2.2", recorder
        )
        self.assertEqual(ctx.fromip, "2.2.2.2")
        return

    def test_owner_returns_live_reference(self) -> None:
        """
            Verify ``owner`` returns the live owner object while it exists.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        self.assertIs(ctx.owner, owner)
        return

    def test_owner_returns_none_after_owner_deleted(self) -> None:
        """
            Verify ``owner`` returns ``None`` after the original reference is
            garbage-collected.
        """
        owner = DummyOwner()
        recorder = _DestroyRecorder()
        ctx = trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", recorder
        )
        del owner
        gc.collect()
        self.assertIsNone(ctx.owner)
        return


if __name__ == "__main__":
    unittest.main()
