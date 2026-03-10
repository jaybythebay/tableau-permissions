"""User-related methods for Tableau Online."""

from typing import Any, List

import tableauserverclient as TSC
from src.exceptions import TooManyGroupsException, NoDefaultGroupException


class User:
    """Methods and properties for a single user in Tableau Online."""

    def __init__(self, server: Any, user_email: str) -> None:
        """Initialize the User helper for a given email.

        Args:
            server: Tableau server connection (authenticated).
            user_email: Email address of the user in Tableau Online.

        Raises:
            IndexError: If no user is found for the given email.
        """
        self.server = server
        tableau_user = str(user_email)
        self._req_option = TSC.RequestOptions()
        self._req_option.filter.add(
            TSC.Filter(
                TSC.RequestOptions.Field.Name,
                TSC.RequestOptions.Operator.Equals,
                tableau_user,
            )
        )
        self.user = self.server.users.get(self._req_option)[0][0]

    def get_role(self) -> str:
        """Return the site role for this user.

        Returns:
            The user's site role string, or 'None' if the user cannot be fetched.
        """
        try:
            role = self.server.users.get(self._req_option)[0][0].site_role
        except Exception:
            print('User does not exist.')
            role = 'None'
        return role

    def get_groups(self) -> List[str]:
        """Return the list of group names this user belongs to.

        Returns:
            List of group name strings; may be empty if populate fails.
        """
        groups: List[str] = []
        try:
            self.server.users.populate_groups(self.user)
            for group in self.user.groups:
                groups.append(group._name)
        except Exception:
            print('User is missing required ID.')
        return groups

    def audit_groups(self) -> None:
        """Ensure the user is in at most two groups and is in the default 'All Users' group.

        Raises:
            TooManyGroupsException: If the user is in more than two groups.
            NoDefaultGroupException: If the user is not in the 'All Users' group.
        """
        try:
            groups: list = self.get_groups()
            if len(groups) > 2:
                raise TooManyGroupsException
                print(groups)
            elif 'All Users' not in groups:
                raise NoDefaultGroupException
            else:
                pass
        except TooManyGroupsException:
            raise TooManyGroupsException
        except NoDefaultGroupException:
            raise NoDefaultGroupException
        else:
            pass
