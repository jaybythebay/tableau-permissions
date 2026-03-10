"""Add, remove, and modify permissions for groups in Tableau projects."""

from typing import Any, Dict, List

import tableauserverclient as TSC

from src.groups import Groups
from src.projects import Projects
from configs.permission_sets import (
    project_none_all,
    workbook_none_all,
    datasource_none_all,
    flow_none_all,
    metric_none_all,
)


class Permissions:
    """Manage project-level permissions (project, workbook, datasource, flow, metric)."""

    def __init__(self, server: Any, show_logging: bool = True) -> None:
        """Initialize the Permissions helper.

        Args:
            server: The Tableau server connection (authenticated).
            show_logging: If True, print permission operations to the console.
        """
        self.server = server
        self.show_logging = show_logging

    def extract_permission_sets(
        self,
        populated_permission_area: List[Any],
        print_logging: bool = True,
    ) -> Dict[str, Any]:
        """Turn TSC permission rules into a dict of grantee id -> capabilities.

        Args:
            populated_permission_area: List of TSC permission rule objects (e.g. from populate_*_default_permissions).
            print_logging: If True, print grantee id and capabilities.

        Returns:
            Dict mapping grantee id to capabilities dict (e.g. {'Read': 'Allow', 'Write': 'Deny'}).
        """

        project_permissions = {}
        for permission in populated_permission_area:

            if print_logging:
                print(permission.grantee.id, permission.capabilities)

            project_permissions[permission.grantee.id] = permission.capabilities

        return project_permissions

    def get_all_project_permissions(
        self,
        permissions_area: str,
        print_logging: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch current permissions for the given area across all projects.

        Args:
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.
            print_logging: If True, print progress to the console.

        Returns:
            Nested dict: project name -> group id -> capabilities dict. Projects that fail
            to load (e.g. server error) get an empty dict for that area.
        """

        projects = Projects(self.server).get_all_projects()

        permission_sets = {}

        print_logging = True

        for project in projects:

            if print_logging:
                print('-' * 15, 'PROJECT: ', project.name, '-' * 15)

            project_permissions = {}

            try:
                # Populate area specific permissions
                if permissions_area == 'project':
                    self.server.projects.populate_permissions(project)
                    project_permissions = self.extract_permission_sets(
                        populated_permission_area=project.permissions, print_logging=True)
                elif permissions_area == 'workbook':
                    self.server.projects.populate_workbook_default_permissions(project)
                    project_permissions = self.extract_permission_sets(
                        populated_permission_area=project.default_workbook_permissions, print_logging=True)
                elif permissions_area == 'datasource':
                    self.server.projects.populate_datasource_default_permissions(project)
                    project_permissions = self.extract_permission_sets(
                        populated_permission_area=project.default_datasource_permissions, print_logging=True)
                elif permissions_area == 'flow':
                    self.server.projects.populate_flow_default_permissions(project)
                    project_permissions = self.extract_permission_sets(
                        populated_permission_area=project.default_flow_permissions, print_logging=True)
                elif permissions_area == 'metric':
                    self.server.projects.populate_metric_default_permissions(project)
                    project_permissions = self.extract_permission_sets(
                        populated_permission_area=project.default_metric_permissions, print_logging=True)
            except TSC.ServerResponseError as e:
                print(f"Warning: could not get {permissions_area} permissions for project '{project.name}' (server error); skipping. {e}")
                project_permissions = {}

            permission_sets[project.name] = project_permissions

        return permission_sets

    def prepare_permissions_subset(
        self,
        permission_set: Dict[str, Any],
        permissions_area: str,
        print_logging: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """Build a permission subset from config, keyed by project then group id (not name).

        Groups not found on the server are skipped with a warning. Projects with no valid
        groups are skipped.

        Args:
            permission_set: Config dict: project name -> group name -> settings (with permissions_area key).
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.
            print_logging: If True, print progress.

        Returns:
            Dict: project name -> { group_id: capabilities_dict }.
        """

        groups_names_and_ids = Groups(self.server).get_group_names_and_ids()

        new_permissions_set = {}

        for project_names, group_settings in permission_set.items():

            if print_logging:
                print(project_names)
                print(group_settings)

            group_id_project_setting = {}

            for group, settings in group_settings.items():
                if group not in groups_names_and_ids:
                    print(f"Warning: group '{group}' from config not found on server; skipping.")
                    continue
                if print_logging:
                    print(group, groups_names_and_ids[group])
                    print(settings[permissions_area])
                group_id_project_setting[groups_names_and_ids[group]] = settings[permissions_area]

            if print_logging:
                print(group_id_project_setting)

            if not group_id_project_setting:
                print(f"Warning: project '{project_names}' has no groups found on server (all missing); skipping.")
                continue
            new_permissions_set[project_names] = group_id_project_setting

        return new_permissions_set

    def permissions_to_delete(
        self,
        desired_permissions: Dict[str, Dict[str, Any]],
        current_online_permissions: Dict[str, Dict[str, Any]],
        print_logging: bool = False,
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Compute which permission rules must be deleted before applying desired state.

        Tableau requires removing existing rules before adding/updating. This returns the
            current values to delete where they differ from desired.

        Args:
            desired_permissions: Target permissions (project -> group_id -> capabilities).
            current_online_permissions: Current permissions from the server (same shape).
            print_logging: If True, print progress.

        Returns:
            Dict of permissions to delete: project -> group_id -> { capability: current_value }.
        """
        print('-' * 100)
        print('-' * 100)
        print('-'*20, "PERMISSIONS TO DELETE", '-'*20)
        print('-' * 100)
        print('-' * 100)

        permissions_to_delete = {}

        # Go through the projects
        for project, group in desired_permissions.items():

            if print_logging:
                print('IDENTIFYING DELETION FOR PROJECT:', project)

            if project not in current_online_permissions:
                print(f"Warning: project '{project}' not in current online permissions; skipping.")
                continue

            # Go through the groups
            group_permissions = {}
            for group_id, permission_settings in group.items():

                group_permissions[group_id] = {}

                # Go through the permissions items
                settings_to_change = {}

                if permission_settings is not None:
                    for permission, setting in permission_settings.items():

                        delete_permission = False

                        # If the group has no permissions for the project then there's nothing to delete
                        if group_id in current_online_permissions[project]:

                            # If the key isn't in the dictionary we don't need to remove any permissions from
                            # Tableau Online as they are None
                            if permission in current_online_permissions[project][group_id]:

                                if setting != current_online_permissions[project][group_id][permission]:
                                    delete_permission = True
                                    settings_to_change[permission] = current_online_permissions[project][group_id][
                                        permission]

                                if print_logging:
                                    if delete_permission:
                                        print(project, group_id, permission, 'DESIRED:', setting, 'CURRENT:',
                                              current_online_permissions[project][group_id][permission],
                                              'CHANGE PERMISSION:',
                                              delete_permission)
                                    else:
                                        print(project, group_id, permission, 'DESIRED:', setting, 'CURRENT:',
                                              current_online_permissions[project][group_id][permission])

                if print_logging:
                    print(settings_to_change)
                group_permissions[group_id] = settings_to_change

            if print_logging:
                print(group_permissions)
            permissions_to_delete[project] = group_permissions

        return permissions_to_delete

    def delete_permissions(
        self,
        permissions_set: Dict[str, Dict[str, Any]],
        permissions_area: str,
        print_logging: bool,
    ) -> None:
        """Remove the given permission rules from the server for the specified area.

        Args:
            permissions_set: Dict from permissions_to_delete: project -> group_id -> capabilities to remove.
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.
            print_logging: If True, print each deletion.

        Returns:
            None.
        """

        print('-' * 100)
        print('-' * 100)
        print('-'*20, "DELETE PERMISSIONS", '-'*20)
        print('-' * 100)
        print('-' * 100)
        groups = Groups(self.server).get_group_ids_and_names()
        project_names = {p.name for p in Projects(self.server).get_all_projects()}

        for project, group in permissions_set.items():
            if project not in project_names:
                print(f"Warning: project '{project}' not found on server; skipping delete for this project.")
                continue
            for group_id, permissions in group.items():
                if group_id not in groups:
                    print(f"Warning: group id '{group_id}' not found on server; skipping delete for this group.")
                    continue
                if len(permissions) > 0:
                    for permission, setting in permissions.items():
                        print(project, group_id, permission, setting)

                        # Get the project and the appropriate permission rules for this area
                        project_item = Projects(self.server).get_project(project)
                        if permissions_area == 'project':
                            self.server.projects.populate_permissions(project_item)
                            permission_rules = project_item.permissions
                        elif permissions_area == 'workbook':
                            self.server.projects.populate_workbook_default_permissions(project_item)
                            permission_rules = project_item.default_workbook_permissions
                        elif permissions_area == 'datasource':
                            self.server.projects.populate_datasource_default_permissions(project_item)
                            permission_rules = project_item.default_datasource_permissions
                        elif permissions_area == 'flow':
                            self.server.projects.populate_flow_default_permissions(project_item)
                            permission_rules = project_item.default_flow_permissions
                        elif permissions_area == 'metric':
                            self.server.projects.populate_metric_default_permissions(project_item)
                            permission_rules = project_item.default_metric_permissions
                        else:
                            print(f"Warning: unsupported permissions_area '{permissions_area}' in delete_permissions.")
                            continue

                        project_capabilities = {permission: setting}

                        for permission_item in permission_rules:
                            if permission_item.grantee.id == group_id:
                                rules_to_delete = TSC.PermissionsRule(
                                    grantee=permission_item.grantee,
                                    capabilities=project_capabilities,
                                )

                                if print_logging:
                                    print(
                                        f"Group: {groups[group_id]}: {permissions_area.capitalize()} "
                                        f"(Project {project_item.id}) Removing {permission}"
                                    )
                                    print(
                                        "TRYING TO REMOVE PERMISSIONS FOR: ",
                                        project,
                                        "GROUP:",
                                        groups[group_id],
                                        "PERMISSIONS AREA:",
                                        permissions_area,
                                        "PERMISSIONS REMOVED:",
                                        permission,
                                        setting,
                                    )

                                if permissions_area == 'project':
                                    response = self.server.projects.delete_permission(project_item, rules_to_delete)

                                elif permissions_area == 'workbook':
                                    response = self.server.projects.delete_workbook_default_permissions(project_item,
                                                                                                        rules_to_delete)

                                elif permissions_area == 'datasource':
                                    response = self.server.projects.delete_datasource_default_permissions(
                                        project_item, rules_to_delete)

                                elif permissions_area == 'flow':
                                    response = self.server.projects.delete_flow_default_permissions(project_item,
                                                                                                    rules_to_delete)

                                elif permissions_area == 'metric':
                                    response = self.server.projects.delete_metric_default_permissions(project_item,
                                                                                                    rules_to_delete)

                                if print_logging:
                                    print("REMOVED PERMISSIONS FOR: ", project, "GROUP:", groups[group_id],
                                          'PERMISSIONS AREA:', permissions_area, 'PERMISSIONS REMOVED:', permission,
                                          setting)
                                    print(response)

        return None

    def add_permissions(
        self,
        permission_set: Dict[str, Dict[str, Any]],
        permissions_area: str,
        print_logging: bool = False,
    ) -> None:
        """Apply permission rules for the given area (project -> group id -> capabilities).

        Args:
            permission_set: Dict mapping project name to group_id -> capabilities dict.
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.
            print_logging: If True, print each add.

        Returns:
            None.
        """

        print('-' * 100)
        print('-' * 100)
        print('-'*20, "ADD PERMISSIONS", '-'*20)
        print('-' * 100)
        print('-' * 100)

        projects = Projects(self.server).get_all_projects()
        groups = Groups(self.server).get_all_groups()
        group_objects = Groups(self.server).get_group_configs()

        for each_project, each_group_setting in permission_set.items():

            if print_logging:
                print(each_project)

            project_matches = list(filter(lambda x: x.name == each_project, projects))
            if not project_matches:
                print(f"Warning: project '{each_project}' from config not found on server; skipping.")
                continue
            project = project_matches[0]

            for each_group, each_setting in each_group_setting.items():
                group_matches = list(filter(lambda x: x._id == each_group, groups))
                if not group_matches:
                    print(f"Warning: group id '{each_group}' not found on server; skipping.")
                    continue
                group_id = group_matches[0]
                group_name = [n['name'] for n in group_objects if n['id'] == each_group]

                if print_logging:
                    print('PROJECT_NAME:', each_project, 'GROUP_ID:', each_group, 'GROUP_NAME:', group_name,
                          'SETTINGS:', each_setting)

                try:
                    rule = TSC.PermissionsRule(grantee=group_id, capabilities=each_setting)
                    if permissions_area == 'project':
                        self.server.projects.update_permissions(project, [rule])
                    elif permissions_area == 'workbook':
                        self.server.projects.update_workbook_default_permissions(project, [rule])
                    elif permissions_area == 'datasource':
                        self.server.projects.update_datasource_default_permissions(project, [rule])
                    elif permissions_area == 'flow':
                        self.server.projects.update_flow_default_permissions(project, [rule])
                    elif permissions_area == 'metric':
                        self.server.projects.update_metric_default_permissions(project, [rule])
                except TSC.ServerResponseError as e:
                    # Some Tableau sites do not support all default-permission endpoints
                    # (for example, Data Roles) and will return 405 Method Not Allowed.
                    print(
                        f"Warning: could not update {permissions_area} permissions for project "
                        f"'{each_project}' and group id '{each_group}'; skipping. {e}"
                    )

    def add_permissions_sequence(
        self,
        permission_set: Dict[str, Any],
        permissions_area: str,
    ) -> None:
        """Sync permissions for the given area to match config (delete then add).

        Prepares subset from config, fetches current permissions, computes deletions,
        deletes then adds so the server matches the desired state.

        Args:
            permission_set: Config dict: project name -> group name -> settings (incl. permissions_area).
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.

        Returns:
            None.
        """

        permissions_set_subset = self.prepare_permissions_subset(permission_set=permission_set,
                                                                 permissions_area=permissions_area,
                                                                 print_logging=True)

        current_online_permissions = self.get_all_project_permissions(permissions_area=permissions_area,
                                                                      print_logging=True)

        permissions_to_delete = self.permissions_to_delete(desired_permissions=permissions_set_subset,
                                                           current_online_permissions=current_online_permissions,
                                                           print_logging=True)

        self.delete_permissions(permissions_set=permissions_to_delete, permissions_area=permissions_area,
                                print_logging=True)

        self.add_permissions(permission_set=permissions_set_subset, permissions_area=permissions_area,
                             print_logging=True)

        return None

    def list_projects_for_group(
        self,
        permissions_area: str,
        group_name: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Return projects where the given group has explicit permissions for the area.

        Args:
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.
            group_name: Name of the Tableau group (e.g. 'All Users').

        Returns:
            Dict mapping project name to that group's capabilities dict for the area.
        """
        groups_helper = Groups(self.server)
        names_to_ids = groups_helper.get_group_names_and_ids()
        if group_name not in names_to_ids:
            print(f"Warning: group '{group_name}' not found on server; nothing to list.")
            return {}
        group_id = names_to_ids[group_name]

        all_perms = self.get_all_project_permissions(permissions_area=permissions_area, print_logging=False)
        result: Dict[str, Dict[str, Any]] = {}
        for project_name, group_map in all_perms.items():
            caps = group_map.get(group_id)
            if caps:
                result[project_name] = caps
        return result

    def clear_group_permissions(
        self,
        permissions_area: str,
        group_name: str,
        print_logging: bool = True,
    ) -> None:
        """Set permissions for a group to the *_none_all template across all projects for the area.

        This replaces existing explicit capabilities for the given group in the specified
        area with the corresponding *_none_all permission set from configs/permission_sets.py.

        Args:
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'datarole', 'metric'.
            group_name: Name of the Tableau group (e.g. 'All Users').
            print_logging: If True, print progress.

        Returns:
            None.
        """
        none_templates = {
            'project': project_none_all,
            'workbook': workbook_none_all,
            'datasource': datasource_none_all,
            'flow': flow_none_all,
            'metric': metric_none_all,
        }
        if permissions_area not in none_templates:
            print(f"Warning: unsupported permissions_area '{permissions_area}' for clear_group_permissions.")
            return None
        none_caps = none_templates[permissions_area]

        groups_helper = Groups(self.server)
        names_to_ids = groups_helper.get_group_names_and_ids()
        group_id = names_to_ids.get(group_name)
        if not group_id:
            print(f"Warning: group '{group_name}' not found on server; nothing to clear.")
            return None

        all_perms = self.get_all_project_permissions(permissions_area=permissions_area, print_logging=False)
        to_update: Dict[str, Dict[str, Any]] = {}
        for project_name, group_map in all_perms.items():
            caps = group_map.get(group_id)
            if caps:
                if project_name not in to_update:
                    to_update[project_name] = {}
                to_update[project_name][group_id] = none_caps

        if not to_update:
            print(f"No explicit permissions for group '{group_name}' in area '{permissions_area}' to replace.")
            return None

        self.add_permissions(
            permission_set=to_update,
            permissions_area=permissions_area,
            print_logging=print_logging,
        )

        return None

    def delete_group_permissions_only(
        self,
        permissions_area: str,
        group_name: str,
        print_logging: bool = True,
    ) -> None:
        """Delete explicit permissions for a group across all projects for the area.

        This uses the existing delete_permissions() flow, removing any explicit
        rules for the given group and area without attempting to set them to None.

        Args:
            permissions_area: One of 'project', 'workbook', 'datasource', 'flow', 'metric'.
            group_name: Name of the Tableau group (e.g. 'All Users').
            print_logging: If True, print progress.

        Returns:
            None.
        """
        groups_helper = Groups(self.server)
        names_to_ids = groups_helper.get_group_names_and_ids()
        group_id = names_to_ids.get(group_name)
        if not group_id:
            print(f"Warning: group '{group_name}' not found on server; nothing to clear.")
            return None

        all_perms = self.get_all_project_permissions(
            permissions_area=permissions_area,
            print_logging=False,
        )
        to_update: Dict[str, Dict[str, Any]] = {}
        for project_name, group_map in all_perms.items():
            caps = group_map.get(group_id)
            if caps:
                if project_name not in to_update:
                    to_update[project_name] = {}
                # Use the current capabilities as the set to delete.
                to_update[project_name][group_id] = caps

        if not to_update:
            print(f"No explicit permissions for group '{group_name}' in area '{permissions_area}' to delete.")
            return None

        self.delete_permissions(
            permissions_set=to_update,
            permissions_area=permissions_area,
            print_logging=print_logging,
        )

        return None
