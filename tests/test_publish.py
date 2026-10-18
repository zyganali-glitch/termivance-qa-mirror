import pytest

from termivance.publish import GitLabPublisher


def test_publisher_refuses_non_report_endpoint():
    publisher = GitLabPublisher("t")
    with pytest.raises(PermissionError):
        publisher._post("/projects/1/pages", {})
    with pytest.raises(PermissionError):
        publisher._post("/projects/1", {})


def test_publisher_allows_issue_and_note_endpoints():
    publisher = GitLabPublisher("t")
    assert "/projects/1/issues".endswith(publisher.ALLOWED_ENDPOINTS_SUFFIX)
    assert "/projects/1/issues/2/notes".endswith(publisher.ALLOWED_ENDPOINTS_SUFFIX)
