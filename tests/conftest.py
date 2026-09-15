"""
Session-wide test isolation.

Setting OMNIAGENT_DATA_DIR here, before any test module gets a chance to
import `config` (and therefore `config.env`, which creates data directories
at import time), means the test suite never depends on the real default
location (~/.local/share/omniagent) being writable. Verification against a
real machine surfaced this as a real failure mode: a read-only or
permission-restricted home directory made every test that transitively
imports `config` fail at collection time, well before the test itself ran.

Uses os.environ.setdefault rather than a plain assignment so an operator who
explicitly sets OMNIAGENT_DATA_DIR themselves (to inspect what the test run
actually wrote, for example) isn't silently overridden.
"""
import os
import tempfile

os.environ.setdefault("OMNIAGENT_DATA_DIR", tempfile.mkdtemp(prefix="omniagent-test-data-"))
