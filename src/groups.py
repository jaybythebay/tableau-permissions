"""Create and view groups in Tableau Online."""

from typing import Any, Dict, List

import tableauserverclient as TSC

from src.exceptions import TooManyGroupsException, NoDefaultGroupException, IncorrectExecutiveMemberException
from src.users import User
from configs.executive_membership import executive_members


class Groups:
    """Gets, creates, and updates Tableau Online groups."""

    def __init__(self, server: Any, show_logging: bool = True) -> None:
        """Initialize the Groups helper.

        Args:
            server: The Tableau server connection (authenticated).
            show_logging: If True, print group info to the console.
        """
        self.server = server
        self.show_logging = show_logging

    def get_all_groups(self) -> List[Any]:
        """Fetch all groups from the Tableau server.

        Returns:
            List of TSC GroupItem objects from the server.
        """
        return list(TSC.Pager(self.server.groups))

    def get_group_configs(self) -> List[Dict[str, Any]]:
        """Build a list of group dicts with name, id, description (domain_name), etc.

        Returns:
            List of dicts with keys: name, id, description, parent_id, content_permissions.
        """
        groups = []

        all_groups = self.get_all_groups()

        for each_group in all_groups:

            if self.show_logging:
                print(each_group.name)
                print(each_group.id)
                print(each_group.domain_name)
                print(each_group.minimum_site_role)
                print(each_group.license_mode)
                print("-" * 5)

            group = {'name': each_group.name,
                     'id': each_group.id,
                     'description': each_group.domain_name,
                     'parent_id': each_group.minimum_site_role,
                     'content_permissions': each_group.license_mode
                     }

            groups.append(group)

        return groups

    def create_group(self, name: str) -> None:
        """Create a group with the given name on the server.

        Args:
            name: Display name of the group to create.

        Returns:
            None.
        """
        newgroup = TSC.GroupItem(name)
        self.server.groups.create(newgroup)
        print('Created group of:', name)

        return None

    def get_group_names(self) -> List[str]:
        """Get a list of all group names on the server.

        Returns:
            List of group name strings.
        """
        groups = self.get_group_configs()

        name_list = []

        for group in groups:
            name_list.append(group['name'])

        return name_list


    def get_group_names_and_ids(self) -> Dict[str, str]:
        """Build a mapping of group name to group id for lookups.

        Returns:
            Dict mapping group name to id, e.g. {'Group A': 'abc-123', 'Group B': 'def-456'}.
        """
        groups = self.get_group_configs()
        groups_names_and_ids = {}
        for group in groups:
            groups_names_and_ids[group['name']] = group['id']

        return groups_names_and_ids

    def get_group_ids_and_names(self) -> Dict[str, str]:
        """Build a mapping of group id to group name for lookups.

        Returns:
            Dict mapping group id to name, e.g. {'abc-123': 'Group A', 'def-456': 'Group B'}.
        """
        groups = Groups(self.server, show_logging=False).get_group_configs()
        groups_ids_and_names = {}
        for group in groups:
            groups_ids_and_names[group['id']] = group['name']

        return groups_ids_and_names

    def audit_all_groups(self) -> None:
        """Audit group membership for all users on the server.

        For each user, runs audit_groups(). If a user is in the Executive group but not in
        configs/executive_membership.py, raises IncorrectExecutiveMemberException. Handles
        TooManyGroupsException and NoDefaultGroupException by printing messages.

        Returns:
            None.
        """
        all_users, pagination_item = self.server.users.get()
        for user in all_users:
            user_object = User(self.server, user.name)
            try:
                user_object.audit_groups()
                groups = user_object.get_groups()
                if 'Executive' in groups and user.name not in executive_members:
                    raise IncorrectExecutiveMemberException
            except TooManyGroupsException:
                print(f'{user.name} is in too many groups.')
            except NoDefaultGroupException:
                print(f'{user.name} is not in the Default group.')
            except IncorrectExecutiveMemberException:
                print(f'{user.name} is in the Executive group and should not be.')
