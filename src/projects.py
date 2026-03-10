"""Create and view projects in Tableau Online."""

from typing import Any, Dict, Iterable, List, Optional

import tableauserverclient as TSC


class Projects:
    """Gets, creates, and updates Tableau Online projects."""

    def __init__(self, server: Any, show_logging: bool = True) -> None:
        """Initialize the Projects helper.

        Args:
            server: The Tableau server connection (authenticated).
            show_logging: If True, print project info to the console.
        """
        self.server = server
        self.show_logging = show_logging

    def get_all_projects(self) -> List[Any]:
        """Fetch all projects from the Tableau server.

        Returns:
            List of TSC ProjectItem objects from the server.
        """
        return list(TSC.Pager(self.server.projects))

    def get_project_configs(self) -> List[Dict[str, Any]]:
        """Build a list of project dicts with id, name, description, parent_id, content_permissions.

        Returns:
            List of dicts with keys: id, name, description, parent_id, content_permissions.
        """
        all_projects = self.get_all_projects()

        projects = []

        for project in all_projects:

            if self.show_logging:
                print("-" * 5)
                print(project.name)
                print(project.id)
                print(project.description)
                print(project.parent_id)
                print(project.content_permissions)

            project = {'id': project.id,
                       'name': project.name,
                       'description': project.description,
                       'parent_id': project.parent_id,
                       'content_permissions': project.content_permissions
                       }

            projects.append(project)

        return projects

    def create_project(self, name: str, description: str) -> Optional[Any]:
        """Create a top-level project with the given name and description.

        Args:
            name: Display name of the project.
            description: Description text for the project.

        Returns:
            The created ProjectItem, or None if creation failed (e.g. already exists).
        """
        project_item = TSC.ProjectItem(name=name, description=description, content_permissions='LockedToProject')
        try:
            project_item = self.server.projects.create(project_item)
            print(f'Created a new project called: {project_item.name}')
            return project_item
        except TSC.ServerResponseError:
            print('We have already created this project: {project_item.name}')

        return None

    def get_project_names(self, top_level_only: bool = True) -> List[str]:
        """Get project names, optionally limited to top-level projects only.

        Args:
            top_level_only: If True, return only projects with no parent_id.

        Returns:
            List of project name strings.
        """

        projects = self.get_project_configs()

        name_list = []

        for project in projects:
            if top_level_only:
                if project['parent_id'] is None:
                    name_list.append(project['name'])
            else:
                name_list.append(project['name'])

        if self.show_logging:
            print(name_list)

        return name_list

    def get_project(self, name: str) -> Optional[Any]:
        """Return the Tableau ProjectItem for a project with the given name.

        Args:
            name: The project name to look up.

        Returns:
            The ProjectItem whose name matches, or None if no match.
        """
        projects = self.get_all_projects()
        project_object = None
        for project in projects:
            if project.name == name:
                project_object = project
        return project_object

    def audit_projects(
        self,
        config_project_names: Iterable[str],
        protected_names: Iterable[str],
    ) -> List[Dict[str, str]]:
        """Compare config project names to server (full outer join).

        Args:
            config_project_names: Iterable of project names from config (e.g. top_level_projects).
            protected_names: Iterable of project names that are protected (never create/delete).

        Returns:
            List of dicts with keys: project, in_config, on_server, protected (for tabulate or display).
        """
        config_set = set(config_project_names)
        protected_set = set(protected_names)
        projects = self.get_project_configs()
        online_top_level = {p['name'] for p in projects if p['parent_id'] is None}
        all_names = config_set | online_top_level
        rows = []
        for name in sorted(all_names):
            rows.append({
                'project': name,
                'in_config': 'Yes' if name in config_set else 'No',
                'on_server': 'Yes' if name in online_top_level else 'No',
                'protected': 'Yes' if name in protected_set else 'No',
            })
        return rows
