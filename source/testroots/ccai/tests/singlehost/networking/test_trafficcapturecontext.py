"""
    .. module:: test_trafficcapturecontext
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the
            :mod:`ccai.networking.trafficcapturecontext` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import gc

from ccai.networking import trafficcapturecontext


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


def test_noncallable_destroy_method_raises_value_error() -> None:
    """
        Verify a ``None`` destroy method raises ``ValueError``.
    """
    owner = DummyOwner()
    raised = False
    try:
        trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", None
        )
    except ValueError:
        raised = True

    assert raised
    return


def test_non_callable_destroy_method_raises_value_error() -> None:
    """
        Verify a non-callable destroy method raises ``ValueError``.
    """
    owner = DummyOwner()
    raised = False
    try:
        trafficcapturecontext.TrafficCaptureContext(
            owner, "sid", "1.1.1.1", "not-callable"
        )
    except ValueError:
        raised = True

    assert raised
    return


def test_enter_returns_self() -> None:
    """
        Verify ``__enter__`` returns the context instance.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "sid", "1.1.1.1", recorder
    )
    with ctx as captured:
        assert captured is ctx
        assert recorder.call_count == 0
    assert recorder.called_with is ctx
    assert recorder.call_count == 1
    return


def test_exit_calls_destroy_method_on_normal_exit() -> None:
    """
        Verify the destroy method runs when the with-block exits cleanly.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "sid", "1.1.1.1", recorder
    )
    rtnval = ctx.__exit__(None, None, None)
    assert not rtnval
    assert recorder.called_with is ctx
    return


def test_exit_calls_destroy_method_on_exception_path() -> None:
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

    assert raised
    assert recorder.call_count == 1
    assert recorder.called_with is ctx
    return


def test_captures_starts_empty() -> None:
    """
        Verify the captures list is empty on construction.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "sid", "1.1.1.1", recorder
    )
    rtnval = ctx.captures
    assert rtnval == []
    return


def test_append_capture_records_tuple() -> None:
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
    assert len(captures) == 1
    assert captures[0] == (headers, body)
    return


def test_captures_property_returns_a_copy() -> None:
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
    assert len(ctx.captures) == 1
    return


def test_append_capture_returns_none() -> None:
    """
        Verify ``append_capture`` returns ``None``.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "sid", "1.1.1.1", recorder
    )
    rtnval = ctx.append_capture({}, "")
    assert rtnval is None
    return


def test_identifier_returns_supplied_value() -> None:
    """
        Verify the ``identifier`` property echoes the constructor argument.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "identifier", "2.2.2.2", recorder
    )
    assert ctx.identifier == "identifier"
    return


def test_fromip_returns_supplied_value() -> None:
    """
        Verify the ``fromip`` property echoes the constructor argument.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "identifier", "2.2.2.2", recorder
    )
    assert ctx.fromip == "2.2.2.2"
    return


def test_owner_returns_live_reference() -> None:
    """
        Verify ``owner`` returns the live owner object while it exists.
    """
    owner = DummyOwner()
    recorder = _DestroyRecorder()
    ctx = trafficcapturecontext.TrafficCaptureContext(
        owner, "sid", "1.1.1.1", recorder
    )
    assert ctx.owner is owner
    return


def test_owner_returns_none_after_owner_deleted() -> None:
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
    assert ctx.owner is None
    return
