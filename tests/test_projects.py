"""Unit tests for src.projects with mocked Tableau API."""

import pytest
from unittest.mock import MagicMock, patch

from src.projects import Projects


@pytest.fixture
def mock_server():
    """Fake Tableau server object."""
    return MagicMock()


@pytest.fixture
def projects(mock_server):
    """Projects instance with logging disabled."""
    return Projects(mock_server, show_logging=False)


@patch("src.projects.TSC.Pager")
def test_get_all_projects(mock_pager, projects, mock_server):
    """get_all_projects returns list from TSC.Pager(server.projects)."""
    mock_item = MagicMock()
    mock_item.name = "TestProject"
    mock_item.id = "proj-123"
    mock_pager.return_value = [mock_item]
    result = projects.get_all_projects()
    mock_pager.assert_called_once_with(mock_server.projects)
    assert len(result) == 1
    assert result[0].name == "TestProject"


def test_get_project_configs(projects, mock_server):
    """get_project_configs returns list of dicts with id, name, description, parent_id, content_permissions."""
    mock_proj = MagicMock()
    mock_proj.id = "p1"
    mock_proj.name = "P1"
    mock_proj.description = "Desc"
    mock_proj.parent_id = None
    mock_proj.content_permissions = "LockedToProject"
    with patch.object(projects, "get_all_projects", return_value=[mock_proj]):
        configs = projects.get_project_configs()
    assert configs == [
        {
            "id": "p1",
            "name": "P1",
            "description": "Desc",
            "parent_id": None,
            "content_permissions": "LockedToProject",
        }
    ]


def test_create_project_success(projects, mock_server):
    """create_project calls server.projects.create and returns the item."""
    mock_item = MagicMock()
    mock_item.name = "NewProj"
    mock_server.projects.create.return_value = mock_item
    with patch("src.projects.TSC.ProjectItem") as mock_psi:
        result = projects.create_project("NewProj", "A description")
    mock_psi.assert_called_once_with(
        name="NewProj", description="A description", content_permissions="LockedToProject"
    )
    assert result == mock_item


def test_create_project_already_exists(projects, mock_server):
    """create_project catches ServerResponseError and returns None."""
    import tableauserverclient as TSC

    mock_server.projects.create.side_effect = TSC.ServerResponseError(409, "exists", "body")
    with patch("src.projects.TSC.ProjectItem"):
        result = projects.create_project("Exists", "Desc")
    assert result is None


def test_get_project_names_top_level_only(projects):
    """get_project_names with top_level_only=True returns only projects with parent_id None."""
    with patch.object(
        projects,
        "get_project_configs",
        return_value=[
            {"name": "A", "parent_id": None},
            {"name": "B", "parent_id": "parent-1"},
        ],
    ):
        names = projects.get_project_names(top_level_only=True)
    assert names == ["A"]


def test_get_project_names_all(projects):
    """get_project_names with top_level_only=False returns all names."""
    with patch.object(
        projects,
        "get_project_configs",
        return_value=[
            {"name": "A", "parent_id": None},
            {"name": "B", "parent_id": "parent-1"},
        ],
    ):
        names = projects.get_project_names(top_level_only=False)
    assert names == ["A", "B"]


def test_get_project(projects):
    """get_project returns the ProjectItem whose name matches."""
    match = MagicMock()
    match.name = "Target"
    other = MagicMock()
    other.name = "Other"
    with patch.object(projects, "get_all_projects", return_value=[other, match]):
        result = projects.get_project("Target")
    assert result.name == "Target"


def test_audit_projects(projects):
    """audit_projects returns full outer join of config vs server with protected flag."""
    with patch.object(
        projects,
        "get_project_configs",
        return_value=[
            {"name": "OnServer", "parent_id": None},
            {"name": "Child", "parent_id": "x"},
        ],
    ):
        rows = projects.audit_projects(
            config_project_names=["InConfig", "OnServer"],
            protected_names=["OnServer"],
        )
    by_name = {r["project"]: r for r in rows}
    assert by_name["InConfig"] == {"project": "InConfig", "in_config": "Yes", "on_server": "No", "protected": "No"}
    assert by_name["OnServer"] == {"project": "OnServer", "in_config": "Yes", "on_server": "Yes", "protected": "Yes"}
