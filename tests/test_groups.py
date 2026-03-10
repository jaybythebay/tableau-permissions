"""Unit tests for src.groups with mocked Tableau API."""

import pytest
from unittest.mock import MagicMock, patch

from src.groups import Groups


@pytest.fixture
def mock_server():
    """Fake Tableau server object."""
    return MagicMock()


@pytest.fixture
def groups(mock_server):
    """Groups instance with logging disabled."""
    return Groups(mock_server, show_logging=False)


@patch("src.groups.TSC.Pager")
def test_get_all_groups(mock_pager, groups, mock_server):
    """get_all_groups returns list from TSC.Pager(server.groups)."""
    mock_item = MagicMock()
    mock_item.name = "TestGroup"
    mock_item.id = "grp-123"
    mock_pager.return_value = [mock_item]
    result = groups.get_all_groups()
    mock_pager.assert_called_once_with(mock_server.groups)
    assert len(result) == 1
    assert result[0].name == "TestGroup"


def test_get_group_configs(groups):
    """get_group_configs returns list of dicts with name, id, description, parent_id, content_permissions."""
    mock_grp = MagicMock()
    mock_grp.name = "G1"
    mock_grp.id = "g1"
    mock_grp.domain_name = "domain"
    mock_grp.minimum_site_role = "Viewer"
    mock_grp.license_mode = "on-login"
    with patch.object(groups, "get_all_groups", return_value=[mock_grp]):
        configs = groups.get_group_configs()
    assert configs == [
        {
            "name": "G1",
            "id": "g1",
            "description": "domain",
            "parent_id": "Viewer",
            "content_permissions": "on-login",
        }
    ]


def test_create_group(groups, mock_server):
    """create_group creates a GroupItem and calls server.groups.create."""
    with patch("src.groups.TSC.GroupItem") as mock_gi:
        groups.create_group("NewGroup")
    mock_gi.assert_called_once_with("NewGroup")
    mock_server.groups.create.assert_called_once()


def test_get_group_names(groups):
    """get_group_names returns list of names from get_group_configs.

    Uses dicts with only the 'name' key (same shape as get_group_configs).
    If get_group_names uses a wrong key (e.g. 'names' or 'nameasdfasdf'), this raises KeyError.
    """
    with patch.object(
        groups,
        "get_group_configs",
        return_value=[{"name": "A"}, {"name": "B"}],
    ):
        names = groups.get_group_names()
    assert names == ["A", "B"]


def test_get_group_names_uses_name_key(groups):
    """get_group_names reads the 'name' key from each group dict (catches typos like 'names')."""
    # Don't mock: use real implementation; mock get_all_groups so configs have correct shape
    mock_grp1 = MagicMock()
    mock_grp1.name = "G1"
    mock_grp1.id = "id1"
    mock_grp1.domain_name = "d1"
    mock_grp1.minimum_site_role = None
    mock_grp1.license_mode = None
    with patch.object(groups, "get_all_groups", return_value=[mock_grp1]):
        names = groups.get_group_names()
    assert names == ["G1"]


def test_get_group_names_and_ids(groups):
    """get_group_names_and_ids returns dict name -> id."""
    with patch.object(
        groups,
        "get_group_configs",
        return_value=[{"name": "A", "id": "id-a"}, {"name": "B", "id": "id-b"}],
    ):
        d = groups.get_group_names_and_ids()
    assert d == {"A": "id-a", "B": "id-b"}


def test_get_group_ids_and_names(groups):
    """get_group_ids_and_names returns dict id -> name."""
    with patch.object(
        Groups,
        "get_group_configs",
        return_value=[{"name": "A", "id": "id-a"}, {"name": "B", "id": "id-b"}],
    ):
        d = groups.get_group_ids_and_names()
    assert d == {"id-a": "A", "id-b": "B"}
