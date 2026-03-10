# tableau-permissions

Manage Tableau Online/Server projects, groups, and permissions via config and CLI.

## Table of contents

- [About](#about)
- [Setup and usage](#setup-and-usage)
  - [Install](#install)
  - [Setup](#setup)
  - [Configuration](#configuration)
  - [CLI examples](#cli-examples)
- [Develop and contribute](#develop-and-contribute)
  - [Running tests](#running-tests)
- [Acknowledgments](#acknowledgments)

## About

- **Permissions management**: project, workbook, datasource, flow, metric
- **Config-driven**: manage groups, projects, and permissions via Python config files under `configs/`
- **Automation helpers**: audit projects (config vs server), create projects/groups, apply permissions, export existing site config

## Setup and usage

### Install

```bash
pip install tableau-permissions
```

Or from source: `pip install -e .` (then run `tableau-permissions` or `python -m scripts.tableau_setup` from the repo).

### Setup

1. In Tableau Online go to *My Account Settings* and add a *Personal Access Token*.
2. Add these variables to your `.bash_profile`, `.zshenv`, or secrets setup (values shown are examples only):

```commandline
# Tableau Credentials (example values)
export TABLEAU_SERVER_PRODUCTION='https://YOUR-PROD-SERVER.online.tableau.com/'
export TABLEAU_SERVER_TEST='https://YOUR-TEST-SERVER.online.tableau.com/'
export TABLEAU_USERNAME=''
export TABLEAU_PASSWORD=''
export TABLEAU_SITENAME_PRODUCTION=''
export TABLEAU_SITENAME_TEST=''
export TABLEAU_API_VERSION='3.28'
export TABLEAU_PERSONAL_ACCESS_TOKEN_VALUE_PRODUCTION="<your access token here>"
# Make sure the token name matches what you listed when creating the token!
export TABLEAU_PERSONAL_ACCESS_TOKEN_NAME_PRODUCTION="local-dev-token"
export TABLEAU_PERSONAL_ACCESS_TOKEN_VALUE_TEST="<your access token here>"
export TABLEAU_PERSONAL_ACCESS_TOKEN_NAME_TEST='automation-test-token'
```

### Configuration

This repo ships with example configuration files under `configs/`:

- `groups.py` – example department/group names.
- `top_level_projects.py` – example top-level project (folder) structure.
- `project_permissions.py` – example mapping of groups to permissions per project.
- `executive_membership.py` – placeholder list of emails allowed in the `Executive` group.
- `protected_projects.py` – project names that will **not** be created or deleted by this tool (e.g. `default`, `Samples`). Permissions on these projects can still be adjusted.

These are **examples only** and should be customized to match your own organization’s structure and Tableau site.

### CLI examples

Below, `-e test` or `-e prod` selects which Tableau environment to use based on your environment variables.

#### Test authentication only

```commandline
python scripts/tableau_setup.py -e test -ta
```

This will sign in to the specified environment, print basic connection information, and exit without creating projects or changing any permissions.

#### List the projects

```commandline
python scripts/tableau_setup.py -e test -lp
```

### Audit projects (config vs server)

Shows a full outer join of projects in config (`configs/top_level_projects.py`) vs top-level projects on the server, plus whether each is in the protected list:

```commandline
python scripts/tableau_setup.py -e test -ap
```

Output columns: `project`, `in_config`, `on_server`, `protected`. Use this to see what’s missing on the server (in config but not on server) and what exists only on the server (not in config).

Use `--table` to print projects (or groups) as a plain-text table (via `tabulate`) instead of a list. Table output is terminal- and log-friendly (e.g. Airflow):

```commandline
python scripts/tableau_setup.py -e test -lp --table
```

#### Full setup (create projects, create groups, then apply permissions)

On a new or empty Tableau site, run in this order so that projects and groups exist before permissions are applied:

```commandline
python scripts/tableau_setup.py -e test -cp -cg -aap
```

- `-cp` (create projects) – creates top-level projects from `configs/top_level_projects.py` if they don’t exist.
- `-cg` (create groups) – creates groups from `configs/groups.py` if they don’t exist.
- `-aap` (add all permissions) – applies permissions from `configs/project_permissions.py` to those projects and groups. **Requires projects and groups to already exist**; if groups are missing on the server, you’ll see “group … not found on server; skipping” and no permissions will be applied for that project.

#### Add all permissions only (projects and groups already exist)

If projects and groups are already created (e.g. you ran `-cp -cg` earlier or created them in the Tableau UI):

```commandline
python scripts/tableau_setup.py -e test -aap
```

#### Export existing site config to YAML

For a large existing site, you can export the current state (projects, groups, and permissions) to a YAML snapshot as a starting point for configs:

```commandline
python scripts/tableau_setup.py -e prod -ec configs/export
```

This writes `tableau_site_export.yml` under `configs/export/` with:

- `projects`: id, name, description, parent_id, content_permissions
- `groups`: id, name, description/domain_name, minimum_site_role, license_mode
- `permissions`: for each area (`project`, `workbook`, `datasource`, `flow`, `datarole`, `metric`), a mapping of `project -> group -> capabilities`.

#### Inspect and remove `All Users` permissions

To see where the built-in `All Users` group has **explicit project-level permissions**:

```commandline
python scripts/tableau_setup.py -e prod -lpau
```

Add `--table` to see a tabular view.

To remove **all explicit permissions** for `All Users` across all projects (leaving inheritance intact, and skipping virtual connections):

```commandline
python scripts/tableau_setup.py -e prod -cpau
```

This removes explicit rules for the `All Users` group in the `project`, `workbook`, `datasource`, `flow`, and `metric` areas wherever they exist, so permissions fall back to inheritance/defaults.

## Develop and contribute

### Running tests

Install dev dependencies (pytest, pytest-cov, mypy, ruff), then run tests with coverage. **Save your edits first**—pytest runs against the saved files on disk.

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=src --cov-report=term-missing
mypy src scripts  # optional: static type checking
ruff check .      # optional: linting
```

## Acknowledgments

Thanks to [Panther Labs](https://panther.com/) for permitting this code to be open sourced under the MIT license. The original implementation was developed while the author was employed at Panther; the company has kindly allowed it to be released for the community to use and extend.