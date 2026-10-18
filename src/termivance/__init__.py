"""Termivance - Proof-Bounded Software Retirement Protocol.

B2: deterministic Retirement Obligation Graph, read-only GitLab discovery and a
fail-closed retirement decision engine.

B3: an endpoint-restricted GitLab Pages retirement executor
(``DELETE /projects/:id/pages`` only, never a project deletion), exact-target
bounded authorization, and independent bounded-absence observation. A successful
mutation is never treated as proof of absence.
"""

__version__ = "0.3.0"
