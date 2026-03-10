"""
Project names that must never be created or deleted by this tool.
Permissions on these projects can still be adjusted (e.g. via -aap or -pp).
Use this for Tableau-managed projects (e.g. default, Samples) that you want to keep but allow permission changes.
"""
PROTECTED_PROJECTS = frozenset({"default", "Samples", "Admin Insights"})
