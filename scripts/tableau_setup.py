# ruff: noqa: E402

"""
Configures Tableau Projects, Groups, and permissions.

Also supports exporting the current site's groups, projects, and permissions
to a YAML snapshot under configs/ for bootstrapping configs from an existing site.
"""
import os
import sys
from typing import Any, Dict

# Ensure project root is on the path when running as scripts/tableau_setup.py
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import argparse
import yaml
import tableauserverclient as TSC
from tabulate import tabulate

from src.projects import Projects
from src.groups import Groups
from src.permissions import Permissions
from src.users import User
from configs.project_permissions import project_group_permissions
from configs.top_level_projects import top_level_projects
from configs.groups import permission_groups
from configs.protected_projects import PROTECTED_PROJECTS


parser = argparse.ArgumentParser()
audit_vs_add = parser.add_mutually_exclusive_group()  # -ap = audit only, -aap = add all permissions
parser.add_argument('-e', '--environment', type=str, required=True, choices=['prod', 'test'],
                    help='The Tableau environment to run in')
parser.add_argument('-r', '--resource_id', type=str, help='The ID of the resource to view permissions for')
parser.add_argument('-t', '--resource_type', type=str, choices=['workbook', 'datasource', 'flow', 'table', 'database'],
                    help='The type of resource to view permissions for')
parser.add_argument('-p', '--project', type=str, help='The name of the project to view')
parser.add_argument('-cp', '--create_projects', default=False, action='store_true',
                    help='Create the projects if they do not exist')
parser.add_argument('-lp', '--list_projects', default=False, action='store_true',
                    help='List the projects from Tableau Online')
audit_vs_add.add_argument('-ap', '--audit_projects', default=False, action='store_true',
                           help='Audit projects only: full outer join of config vs server (in_config, on_server, protected)')
parser.add_argument('-cg', '--create_groups', default=False, action='store_true',
                    help='Create the groups if they do not exist')
parser.add_argument('-lgn', '--list_group_names', default=False, action='store_true',
                    help='List the groups from Tableau Online')
parser.add_argument('-lgni', '--list_group_names_and_group_ids', default=False, action='store_true',
                    help='List the groups from Tableau Online')
parser.add_argument('-pp', '--add_project_permissions', default=False, action='store_true',
                    help='Add the groups to projects and set project permissions')
parser.add_argument('-wp', '--add_workbook_permissions', default=False, action='store_true',
                    help='Add the workbook permissions for the groups')
parser.add_argument('-dp', '--add_datasource_permissions', default=False, action='store_true',
                    help='Add the datasource permissions for the groups')
parser.add_argument('-fp', '--add_flow_permissions', default=False, action='store_true',
                    help='Add the flow permissions for the groups')
parser.add_argument('-mp', '--add_metric_permissions', default=False, action='store_true',
                    help='Add the metric permissions for the groups')
parser.add_argument('-lpa', '--list_project_permissions_for_area', type=str,
                    choices=['project', 'workbook', 'datasources', 'flow', 'metric'],
                    help='The area you want permissions for: project, workbook, datasource, flow, metric')
audit_vs_add.add_argument('-aap', '--add_all_permissions', default=False, action='store_true',
                           help='Add all permissions for projects, workbooks, flows, etc. (use -ap to audit only)')
parser.add_argument('-lr', '--list_role', type=str, help='List the role for a given user (email) from Tableau Online')
parser.add_argument('-lg', '--list_groups', type=str, help='List the groups for a given user (email) From Tableau Online')
parser.add_argument('-ag', '--audit_groups', type=str, help='Audit the groups for a given user (email) from Tableau Online')
parser.add_argument('-aag', '--audit_all_groups', default=False, action='store_true', help='Audit groups for all users')
parser.add_argument('-ta', '--test_auth', default=False, action='store_true',
                    help='Test authentication only (sign in and exit without making any changes)')
parser.add_argument('-tb', '--table', default=False, action='store_true',
                    help='Print list output (projects, groups) as a plain-text table; works well in logs (e.g. Airflow)')
parser.add_argument(
    '-ec',
    '--export_config',
    type=str,
    default="",
    help='Export current site config (groups, projects, permissions) to a YAML file in this directory',
)
parser.add_argument(
    '-lpau',
    '--list_projects_all_users',
    default=False,
    action='store_true',
    help='List projects where the All Users group has explicit project permissions',
)
parser.add_argument(
    '-cpau',
    '--clear_projects_all_users',
    default=False,
    action='store_true',
    help='Set All Users project-level permissions on all projects to the project_none_all template',
)
args = parser.parse_args()

def setup(environment: str) -> Dict[str, Any]:
    """Load Tableau credentials for the given environment from environment variables.

    Args:
        environment: 'prod' or 'test' (anything other than 'prod' uses test config).

    Returns:
        Credentials dict with server_url, api_version, user_name, password, site_name,
        site_url, token_value, token_name.
    """
    TABLEAU_API_VERSION = os.getenv("TABLEAU_API_VERSION")
    TABLEAU_USERNAME = os.getenv("TABLEAU_USERNAME")
    TABLEAU_PASSWORD = os.getenv("TABLEAU_PASSWORD")

    tableau_server_config = {
        'tableau_prod': {
                'server_url': os.getenv("TABLEAU_SERVER_PRODUCTION"),
                'api_version': TABLEAU_API_VERSION,
                'user_name': TABLEAU_USERNAME,
                'password': TABLEAU_PASSWORD,
                'site_name': os.getenv("TABLEAU_SITENAME_PRODUCTION"),
                'site_url': os.getenv("TABLEAU_SERVER_PRODUCTION"),
                'token_value': os.getenv("TABLEAU_PERSONAL_ACCESS_TOKEN_VALUE_PRODUCTION"),
                'token_name': os.getenv("TABLEAU_PERSONAL_ACCESS_TOKEN_NAME_PRODUCTION"),
        },
        'tableau_test': {
                'server_url': os.getenv("TABLEAU_SERVER_TEST"),
                'api_version': TABLEAU_API_VERSION,
                'user_name': TABLEAU_USERNAME,
                'password': TABLEAU_PASSWORD,
                'site_name': os.getenv("TABLEAU_SITENAME_TEST"),
                'site_url': os.getenv("TABLEAU_SERVER_TEST"),
                'token_value': os.getenv("TABLEAU_PERSONAL_ACCESS_TOKEN_VALUE_TEST"),
                'token_name': os.getenv("TABLEAU_PERSONAL_ACCESS_TOKEN_NAME_TEST"),
        }
    }


    if environment == 'prod':
        credentials = tableau_server_config['tableau_prod']
    else:
        # For anything other than prod, we'll just assume test for safety.
        credentials = tableau_server_config['tableau_test']

    return credentials


def sign_in(connection_information: Dict[str, Any]) -> None:
    """Sign into Tableau Online and run the requested CLI actions.

    Args:
        connection_information: Credentials dict from setup() (server_url, token_name, etc.).

    Returns:
        None.
    """
    print("Site name: ", connection_information['site_name'])
    print("Server URL: ", connection_information['server_url'])
    print("Token name: ", connection_information['token_name'])

    token_value = connection_information.get('token_value') or ''
    if token_value:
        if len(token_value) <= 4:
            masked_token = "*" * len(token_value)
        else:
            masked_token = f"{token_value[0]}***{token_value[-1]}"
        print("Token value (masked): ", masked_token)

    tableau_auth = TSC.PersonalAccessTokenAuth(token_name=connection_information['token_name'],
                                               personal_access_token=connection_information['token_value'],
                                               site_id=connection_information['site_name'])

    server = TSC.Server(connection_information['server_url'], use_server_version=True)
    print(server)

    with server.auth.sign_in(tableau_auth):

        if args.export_config:
            export_dir = args.export_config
            print(f"EXPORT CONFIG to directory: {export_dir}")
            export_site_config(server, export_dir)
            # Export-only mode: do not perform any mutating actions afterwards.
            return None

        if args.list_projects_all_users:
            print("LIST PROJECTS WHERE 'All Users' HAS PROJECT PERMISSIONS")
            perms = Permissions(server, show_logging=False)
            projects = perms.list_projects_for_group(
                permissions_area='project',
                group_name='All Users',
            )
            if args.table:
                rows = [
                    {"project": name, "capabilities": caps}
                    for name, caps in sorted(projects.items())
                ]
                print(tabulate(rows, headers='keys', tablefmt='simple', showindex=False))
            else:
                for name, caps in sorted(projects.items()):
                    print(name, "=>", caps)

        if args.clear_projects_all_users:
            print("CLEARING 'All Users' PERMISSIONS (project, workbook, datasource, flow, metric) ACROSS ALL PROJECTS")
            perms = Permissions(server)
            for area in ['project', 'workbook', 'datasource', 'flow', 'metric']:
                print(f"--- Clearing area: {area} ---")
                perms.delete_group_permissions_only(
                    permissions_area=area,
                    group_name='All Users',
                    print_logging=True,
                )

        if args.test_auth:
            print("Authentication successful for site:", connection_information['site_name'])
            return None

        # Create Top Level Projects in the config if they don't exist in Tableau Online
        if args.create_projects:
            print("CREATE THE PROJECTS")
            project_names = Projects(server).get_project_names(top_level_only=True)
            print(project_names)
            for top_level_project, description in top_level_projects.items():
                if top_level_project in PROTECTED_PROJECTS:
                    print(f"Skipping protected project (will not create): {top_level_project}")
                    continue
                if top_level_project not in project_names:
                    Projects(server).create_project(name=top_level_project, description=description)

        if args.list_projects:
            print("LIST THE PROJECTS")
            if args.table:
                configs = Projects(server, show_logging=False).get_project_configs()
                top_level = [c for c in configs if c['parent_id'] is None]
                rows = [{k: c[k] for k in ('name', 'id', 'description', 'content_permissions')} for c in top_level]
                print(tabulate(rows, headers='keys', tablefmt='simple', showindex=False))
            else:
                project_names = Projects(server).get_project_names(top_level_only=True)
                print(project_names)

        if args.audit_projects:
            print("AUDIT PROJECTS (config vs server, full outer join)")
            config_names = set(top_level_projects.keys())
            rows = Projects(server, show_logging=False).audit_projects(
                config_project_names=config_names,
                protected_names=PROTECTED_PROJECTS,
            )
            print(tabulate(rows, headers='keys', tablefmt='simple', showindex=False))

        if args.create_groups:
            print("CREATE THE GROUPS")
            group_names = Groups(server).get_group_names()
            for group in permission_groups:
                if group not in group_names:
                    Groups(server).create_group(name=group)

        if args.list_group_names:
            print("LIST THE GROUPS")
            if args.table:
                configs = Groups(server, show_logging=False).get_group_configs()
                rows = [{k: c[k] for k in ('name', 'id', 'description')} for c in configs]
                print(tabulate(rows, headers='keys', tablefmt='simple', showindex=False))
            else:
                group_names = Groups(server).get_group_names()
                print(group_names)

        if args.list_group_names_and_group_ids:
            print("LIST THE GROUPS * IDs")
            if args.table:
                configs = Groups(server, show_logging=False).get_group_configs()
                rows = [{k: c[k] for k in ('name', 'id')} for c in configs]
                print(tabulate(rows, headers='keys', tablefmt='simple', showindex=False))
            else:
                groups = Groups(server).get_group_configs()
                for group in groups:
                    print(group['name'], group['id'])

        if args.add_project_permissions:
            print("ADD ALL THE GROUPS TO THE PROJECTS")
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='project')

        if args.add_workbook_permissions:
            print("ADD ALL THE WORKBOOK PERMISSIONS FOR THE GROUPS")
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='workbook')

        if args.add_datasource_permissions:
            print("ADD ALL THE DATASOURCE PERMISSIONS FOR THE GROUPS")
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='datasource')

        if args.add_flow_permissions:
            print("ADD ALL THE FLOW PERMISSIONS FOR THE GROUPS")
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='flow')

        if args.add_metric_permissions:
            print("ADD ALL THE METRIC PERMISSIONS FOR THE GROUPS")
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='metric')

        if args.list_project_permissions_for_area:
            print("LIST THE PROJECT PERMISSIONS:", args.list_project_permissions_for_area)
            Permissions(server).get_all_project_permissions(args.list_project_permissions_for_area)

        if args.add_all_permissions:
            print("ADD ALL THE PERMISSIONS FOR A PROJECT")
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='project')
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='workbook')
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='datasource')
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='flow')
            Permissions(server).add_permissions_sequence(permission_set=project_group_permissions,
                                                         permissions_area='metric')

        if args.list_role:
            print("LIST ALL THE ROLES FOR A USER")
            user_email = str(args.list_role)
            user = User(server, user_email)
            role = user.get_role()
            print(f"USER: {user_email}")
            print(f"ROLE: {role}")

        if args.list_groups:
            print("LIST ALL THE GROUPS FOR A USER")
            user_email = str(args.list_groups)
            user = User(server, user_email)
            groups = user.get_groups()
            print(f"USER: {user_email}")
            print(f"GROUPS: {groups}")

        if args.audit_groups:
            print("AUDIT THE GROUPS FOR A USER")
            user_email = str(args.audit_groups)
            user = User(server, user_email)
            user.audit_groups()

        if args.audit_all_groups:
            print("AUDIT ALL GROUPS FOR ALL USERS")
            Groups(server).audit_all_groups()

    return None


def export_site_config(server: Any, output_dir: str) -> None:
    """Export groups, projects, and permissions from the current site to YAML.

    The YAML snapshot is intended as a starting point for configs on large
    existing sites. It does not attempt to be a perfect round-trip of all
    Tableau concepts, but captures:
      - projects (id, name, description, parent_id, content_permissions)
      - groups (id, name, description/domain_name, minimum_site_role, license_mode)
      - permissions for each area ('project', 'workbook', 'datasource', 'flow',
        'metric') as:
            permissions[area][project_name][group_name] = capabilities_dict
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "tableau_site_export.yml")

    projects_helper = Projects(server, show_logging=False)
    groups_helper = Groups(server, show_logging=False)
    perms_helper = Permissions(server, show_logging=False)

    project_configs = projects_helper.get_project_configs()
    group_configs = groups_helper.get_group_configs()

    # Map group id -> name for readability in exported permissions.
    group_ids_to_names = groups_helper.get_group_ids_and_names()

    permissions_by_area: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
    for area in ['project', 'workbook', 'datasource', 'flow', 'metric']:
        raw = perms_helper.get_all_project_permissions(permissions_area=area, print_logging=False)
        area_map: Dict[str, Dict[str, Dict[str, str]]] = {}
        for project_name, group_id_map in raw.items():
            proj_entry: Dict[str, Dict[str, str]] = {}
            for group_id, caps in group_id_map.items():
                group_name = group_ids_to_names.get(group_id, group_id)
                # caps is already a capability -> setting dict; copy as-is.
                proj_entry[group_name] = caps
            if proj_entry:
                area_map[project_name] = proj_entry
        permissions_by_area[area] = area_map

    snapshot = {
        "projects": project_configs,
        "groups": group_configs,
        "permissions": permissions_by_area,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(snapshot, f, sort_keys=False)

    print(f"Wrote Tableau site snapshot to {out_path}")


def main() -> None:
    tableau_credentials = setup(args.environment)
    sign_in(tableau_credentials)


if __name__ == '__main__':
    main()
