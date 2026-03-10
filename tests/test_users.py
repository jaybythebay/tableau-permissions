"""Unit tests for src.users with mocked Tableau API."""

import pytest
from unittest.mock import MagicMock, patch

from src.users import User
from src.exceptions import TooManyGroupsException, NoDefaultGroupException


@pytest.fixture
def mock_server():
    """Fake Tableau server object."""
    return MagicMock()


@pytest.fixture
def mock_user_item():
    """Fake UserItem for server.users.get."""
    u = MagicMock()
    u.name = "user@example.com"
    u.site_role = "SiteAdministratorExplorer"
    u.groups = []
    return u


def test_user_init(mock_server, mock_user_item):
    """User __init__ fetches user by email and stores it."""
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    assert user.user == mock_user_item


def test_get_role(mock_server, mock_user_item):
    """get_role returns site_role from server.users.get."""
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    role = user.get_role()
    assert role == "SiteAdministratorExplorer"


def test_get_role_user_not_found(mock_server, mock_user_item):
    """get_role returns 'None' when server raises."""
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    mock_server.users.get.side_effect = Exception("400")
    role = user.get_role()
    assert role == "None"


def test_get_groups(mock_server, mock_user_item):
    """get_groups returns list of group names from user.groups."""
    grp = MagicMock()
    grp._name = "All Users"
    mock_user_item.groups = [grp]
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    user.server.users.populate_groups = MagicMock()
    groups = user.get_groups()
    assert groups == ["All Users"]


def test_audit_groups_ok(mock_server, mock_user_item):
    """audit_groups does not raise when user is in <=2 groups and in All Users."""
    mock_user_item.groups = [MagicMock(_name="All Users"), MagicMock(_name="Other")]
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    with patch.object(user, "get_groups", return_value=["All Users", "Other"]):
        user.audit_groups()  # no raise


def test_audit_groups_too_many(mock_server, mock_user_item):
    """audit_groups raises TooManyGroupsException when user is in more than 2 groups."""
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    with patch.object(user, "get_groups", return_value=["All Users", "A", "B"]):
        with pytest.raises(TooManyGroupsException):
            user.audit_groups()


def test_audit_groups_no_default(mock_server, mock_user_item):
    """audit_groups raises NoDefaultGroupException when user is not in All Users."""
    mock_server.users.get.return_value = ([mock_user_item], MagicMock())
    with patch("src.users.TSC.RequestOptions"):
        with patch("src.users.TSC.Filter"):
            user = User(mock_server, "user@example.com")
    with patch.object(user, "get_groups", return_value=["SomeGroup"]):
        with pytest.raises(NoDefaultGroupException):
            user.audit_groups()
