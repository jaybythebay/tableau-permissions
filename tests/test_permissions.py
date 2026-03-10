"""Unit tests for src.permissions with mocked Tableau API."""

import pytest
from unittest.mock import MagicMock, patch

from src.permissions import Permissions


@pytest.fixture
def mock_server():
    """Fake Tableau server object."""
    return MagicMock()


@pytest.fixture
def permissions(mock_server):
    """Permissions instance with logging disabled."""
    return Permissions(mock_server, show_logging=False)


def test_extract_permission_sets(permissions):
    """extract_permission_sets builds grantee id -> capabilities from permission rules."""
    rule1 = MagicMock()
    rule1.grantee.id = "grp-1"
    rule1.capabilities = {"Read": "Allow", "Write": "Deny"}
    rule2 = MagicMock()
    rule2.grantee.id = "grp-2"
    rule2.capabilities = {"Read": "Deny"}
    result = permissions.extract_permission_sets(
        [rule1, rule2],
        print_logging=False,
    )
    assert result == {"grp-1": {"Read": "Allow", "Write": "Deny"}, "grp-2": {"Read": "Deny"}}


def test_prepare_permissions_subset_maps_names_to_ids(permissions):
    """prepare_permissions_subset converts group names to ids and filters by permissions_area."""
    with patch("src.permissions.Groups") as mock_groups_cls:
        mock_groups_cls.return_value.get_group_names_and_ids.return_value = {"GroupA": "id-a", "GroupB": "id-b"}
        result = permissions.prepare_permissions_subset(
            permission_set={
                "Proj1": {
                    "GroupA": {"project": {"Read": "Allow"}, "workbook": {"Read": "Deny"}},
                    "GroupB": {"project": {"Read": "Deny"}, "workbook": {"Read": "Allow"}},
                },
            },
            permissions_area="project",
            print_logging=False,
        )
    assert result == {
        "Proj1": {"id-a": {"Read": "Allow"}, "id-b": {"Read": "Deny"}},
    }


def test_prepare_permissions_subset_skips_missing_groups(permissions):
    """prepare_permissions_subset skips groups not found on server."""
    with patch("src.permissions.Groups") as mock_groups_cls:
        mock_groups_cls.return_value.get_group_names_and_ids.return_value = {"GroupA": "id-a"}
        result = permissions.prepare_permissions_subset(
            permission_set={
                "Proj1": {
                    "GroupA": {"project": {"Read": "Allow"}},
                    "MissingGroup": {"project": {"Read": "Deny"}},
                },
            },
            permissions_area="project",
            print_logging=False,
        )
    assert result == {"Proj1": {"id-a": {"Read": "Allow"}}}


def test_permissions_to_delete_identifies_differences(permissions):
    """permissions_to_delete returns current values where they differ from desired."""
    desired = {
        "P1": {"g1": {"Read": "Allow", "Write": "Deny"}},
    }
    current = {
        "P1": {"g1": {"Read": "Deny", "Write": "Deny"}},
    }
    result = permissions.permissions_to_delete(
        desired_permissions=desired,
        current_online_permissions=current,
        print_logging=False,
    )
    assert result["P1"]["g1"] == {"Read": "Deny"}  # current value to delete for Read


def test_permissions_to_delete_skips_project_not_online(permissions):
    """permissions_to_delete skips projects not in current_online_permissions."""
    desired = {"P1": {"g1": {"Read": "Allow"}}}
    current = {}
    result = permissions.permissions_to_delete(
        desired_permissions=desired,
        current_online_permissions=current,
        print_logging=False,
    )
    assert "P1" not in result


def test_get_all_project_permissions_handles_server_error(permissions, mock_server):
    """get_all_project_permissions treats ServerResponseError as empty permissions for that project."""
    import tableauserverclient as TSC

    mock_proj = MagicMock()
    mock_proj.name = "BadProj"
    with patch("src.permissions.Projects") as mock_projects_cls:
        mock_projects_cls.return_value.get_all_projects.return_value = [mock_proj]
        mock_server.projects.populate_permissions.side_effect = TSC.ServerResponseError(405, "Not Allowed", "body")
        result = permissions.get_all_project_permissions("project", print_logging=False)
    assert result["BadProj"] == {}


def test_add_permissions_calls_update_for_project(permissions, mock_server):
    """add_permissions calls server.projects.update_permissions for project area."""
    mock_proj = MagicMock()
    mock_proj.name = "P1"
    mock_grp = MagicMock()
    mock_grp._id = "g1"
    with patch("src.permissions.Projects") as mock_projects_cls:
        with patch("src.permissions.Groups") as mock_groups_cls:
            mock_projects_cls.return_value.get_all_projects.return_value = [mock_proj]
            mock_projects_cls.return_value.get_project.return_value = mock_proj
            mock_groups_cls.return_value.get_all_groups.return_value = [mock_grp]
            mock_groups_cls.return_value.get_group_configs.return_value = [{"id": "g1", "name": "G1"}]
            permissions.add_permissions(
                permission_set={"P1": {"g1": {"Read": "Allow"}}},
                permissions_area="project",
                print_logging=False,
            )
    mock_server.projects.update_permissions.assert_called_once()


def test_add_permissions_sequence_flows_through(permissions, mock_server):
    """add_permissions_sequence calls prepare, get_all, permissions_to_delete, delete, add."""
    with patch.object(permissions, "prepare_permissions_subset", return_value={"P1": {"g1": {"Read": "Allow"}}}) as mock_prepare:
        with patch.object(permissions, "get_all_project_permissions", return_value={"P1": {"g1": {"Read": "Deny"}}}) as mock_get_all:
            with patch.object(permissions, "permissions_to_delete", return_value={"P1": {"g1": {"Read": "Deny"}}}) as mock_to_del:
                with patch.object(permissions, "delete_permissions") as mock_del:
                    with patch.object(permissions, "add_permissions") as mock_add:
                        permissions.add_permissions_sequence(
                            permission_set={"P1": {"G1": {"project": {"Read": "Allow"}}}},
                            permissions_area="project",
                        )
    mock_prepare.assert_called_once()
    mock_get_all.assert_called_once_with(permissions_area="project", print_logging=True)
    mock_to_del.assert_called_once()
    mock_del.assert_called_once()
    mock_add.assert_called_once()


def test_list_projects_for_group_filters_by_group_name(permissions):
    """list_projects_for_group returns only projects where named group has permissions."""
    with patch("src.permissions.Groups") as mock_groups_cls:
        mock_groups_cls.return_value.get_group_names_and_ids.return_value = {"All Users": "g-all"}
        with patch.object(
            permissions,
            "get_all_project_permissions",
            return_value={
                "P1": {"g-all": {"Read": "Allow"}, "other": {"Read": "Deny"}},
                "P2": {"other": {"Read": "Allow"}},
            },
        ) as mock_get_all:
            result = permissions.list_projects_for_group(permissions_area="project", group_name="All Users")
    mock_get_all.assert_called_once_with(permissions_area="project", print_logging=False)
    assert result == {"P1": {"Read": "Allow"}}


def test_clear_group_permissions_uses_none_template_and_adds(permissions):
    """clear_group_permissions replaces caps with *_none_all template and calls add_permissions."""
    from configs.permission_sets import project_none_all

    with patch("src.permissions.Groups") as mock_groups_cls:
        mock_groups_cls.return_value.get_group_names_and_ids.return_value = {"All Users": "g-all"}
        with patch.object(
            permissions,
            "get_all_project_permissions",
            return_value={
                "P1": {"g-all": {"Read": "Allow"}, "other": {"Read": "Deny"}},
                "P2": {"other": {"Read": "Allow"}},
            },
        ) as mock_get_all, patch.object(permissions, "add_permissions") as mock_add:
            permissions.clear_group_permissions(
                permissions_area="project",
                group_name="All Users",
                print_logging=False,
            )
    mock_get_all.assert_called_once_with(permissions_area="project", print_logging=False)
    mock_add.assert_called_once_with(
        permission_set={"P1": {"g-all": project_none_all}},
        permissions_area="project",
        print_logging=False,
    )


def test_delete_group_permissions_only_builds_delete_set_and_calls_delete(permissions):
    """delete_group_permissions_only looks up group id and delegates to delete_permissions."""
    with patch("src.permissions.Groups") as mock_groups_cls:
        mock_groups_cls.return_value.get_group_names_and_ids.return_value = {"All Users": "g-all"}
        with patch.object(
            permissions,
            "get_all_project_permissions",
            return_value={"P1": {"g-all": {"Read": "Allow"}}},
        ) as mock_get_all, patch.object(permissions, "delete_permissions") as mock_delete:
            permissions.delete_group_permissions_only(
                permissions_area="project",
                group_name="All Users",
                print_logging=False,
            )
    mock_get_all.assert_called_once_with(permissions_area="project", print_logging=False)
    mock_delete.assert_called_once_with(
        permissions_set={"P1": {"g-all": {"Read": "Allow"}}},
        permissions_area="project",
        print_logging=False,
    )


def test_delete_permissions_logs_group_and_permission(permissions, mock_server, capsys):
    """delete_permissions prints an explicit line showing group, area, project id, and permission."""
    # Set up Groups.get_group_ids_and_names and Projects helpers
    with patch("src.permissions.Groups") as mock_groups_cls, patch(
        "src.permissions.Projects"
    ) as mock_projects_cls:
        mock_groups_cls.return_value.get_group_ids_and_names.return_value = {"g-all": "All Users"}

        mock_project = MagicMock()
        mock_project.name = "Sales"
        mock_project.id = "proj-123"
        # Permission rule attached to the project, for the All Users group
        perm_rule = MagicMock()
        perm_rule.grantee.id = "g-all"
        mock_project.permissions = [perm_rule]

        mock_projects_cls.return_value.get_all_projects.return_value = [mock_project]
        mock_projects_cls.return_value.get_project.return_value = mock_project

        # Exercise delete_permissions
        permissions.delete_permissions(
            permissions_set={"Sales": {"g-all": {"ExportImage": "Allow"}}},
            permissions_area="project",
            print_logging=True,
        )

    out, _ = capsys.readouterr()
    assert (
        "Group: All Users: Project (Project proj-123) Removing ExportImage" in out
    ), out
