===========================
Code Craft AI Networking
===========================

The ``codecraftai-networking`` package is the low-level networking toolkit for the ccai suite. It provides the reusable primitives that higher-level protocol, discovery, and landscaping packages build on top of, without pulling in any heavy third-party networking stacks. Downstream packages such as ``codecraftai-interop`` (DNS/mDNS), ``codecraftai-landscaping``, and the various ``codecraftai-interop-ext-*`` packages use these primitives directly.

Highlights
==========

- ``interfaces.py`` for enumerating local network interfaces.
- ``arp.py`` for ARP lookups and ``resolution.py`` for name resolution helpers.
- ``unicast.py``, ``broadcast.py``, and ``multicast.py`` socket-level send/receive helpers across the three delivery modes.
- ``trafficcapturecontext.py`` providing a context-manager-based traffic capture abstraction.
- Zero heavy third-party dependencies — intended as a reusable primitive layer.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/tests/`` - ``unittest``-based tests.
- ``source/examples/`` - Example usage scripts.
- ``specs/`` - Requirements, design, and task documentation.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-environment

Running Tests
=============

Activate the virtual environment:

.. code-block:: bash

   source .venv/bin/activate

Run ``unittest`` tests:

.. code-block:: bash

   python -m unittest discover -s source/tests -p "test_*.py"

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Design documentation: ``specs/design.md``
- Requirements: ``specs/requirements.md``
