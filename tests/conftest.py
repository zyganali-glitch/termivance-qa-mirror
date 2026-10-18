"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from termivance.target import TargetIdentity


@pytest.fixture()
def pages_target() -> TargetIdentity:
    return TargetIdentity(
        project_id=12345678,
        full_path="example-group/example-disposable-pages",
        resource_kind="GITLAB_PAGES_SITE",
    )
