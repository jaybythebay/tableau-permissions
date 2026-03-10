"""
The sets of permissions we can assign for each area out of Project, Workbook, Datasource & Flow.
Permissions are ordered to match the Tableau Online UI. Please preserve that order when adding new permissions.
A mapping is maintained in the Tableau API documentation:
https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_permissions.htm
"""

# Project Permissions Sets
project_deny_all = {"Read": "Deny",
                    "Write": "Deny",
                    }

project_none_all = {"Read": None,
                    "Write": None,
                 }

project_read = {"Read": "Allow",
                "Write": "Deny",
                }

project_write = {"Read": "Allow",
                 "Write": "Allow",
                 }

# Workbook Permission Sets
workbook_deny_all = {
    "Read": "Deny",
    "Filter": "Deny",
    "ViewComments": "Deny",
    "AddComment": "Deny",
    "ExportImage": "Deny",
    "ExportData": "Deny",
    "ExtractRefresh": "Deny",
    "RunExplainData": "Deny",
    "ShareView": "Deny",
    "ViewUnderlyingData": "Deny",
    "WebAuthoring": "Deny",
    "ExportXml": "Deny",
    "Write": "Deny",
    "ChangeHierarchy": "Deny",
    "Delete": "Deny",
    "ChangePermissions": "Deny",
}

workbook_none_all = {
    "Read": None,
    "Filter": None,
    "ViewComments": None,
    "AddComment": None,
    "ExportImage": None,
    "ExportData": None,
    "ExtractRefresh": None,
    "RunExplainData": None,
    "ShareView": None,
    "ViewUnderlyingData": None,
    "WebAuthoring": None,
    "ExportXml": None,
    "Write": None,
    "ChangeHierarchy": None,
    "Delete": None,
    "ChangePermissions": None,
}

workbook_read = {
    "Read": "Allow",
    "Filter": "Allow",
    "ViewComments": "Allow",
    "AddComment": "Allow",
    "ExportImage": "Allow",
    "ExportData": "Allow",
    "ExtractRefresh": "Allow",
    "RunExplainData": "Allow",
    "ShareView": "Allow",
    "ViewUnderlyingData": "Allow",
    "WebAuthoring": "Deny",
    "ExportXml": "Deny",
    "Write": "Deny",
    "ChangeHierarchy": "Deny",
    "Delete": "Deny",
    "ChangePermissions": "Deny",
}

workbook_write = {
    "Read": "Allow",
    "Filter": "Allow",
    "ViewComments": "Allow",
    "AddComment": "Allow",
    "ExportImage": "Allow",
    "ExportData": "Allow",
    "ExtractRefresh": "Allow",
    "RunExplainData": "Allow",
    "ShareView": "Allow",
    "ViewUnderlyingData": "Allow",
    "WebAuthoring": "Allow",
    "ExportXml": "Allow",
    "Write": "Allow",
    "ChangeHierarchy": "Allow",
    "Delete": "Allow",
    "ChangePermissions": "Deny",
}

datasource_deny_all = {
    "Read": "Deny",
    "Connect": "Deny",
    "ExportXml": "Deny",
    "Write": "Deny",
    "SaveAs": "Deny",
    "VizqlDataApiAccess": "Deny",
    "PulseMetricDefine": "Deny",
    "ChangeHierarchy": "Deny",
    "Delete": "Deny",
    "ChangePermissions": "Deny",
    "ExtractRefresh": "Deny",
}

datasource_none_all = {
    "Read": None,
    "Connect": None,
    "ExportXml": None,
    "Write": None,
    "SaveAs": None,
    "VizqlDataApiAccess": None,
    "PulseMetricDefine": None,
    "ChangeHierarchy": None,
    "Delete": None,
    "ChangePermissions": None,
    "ExtractRefresh": None,
}


datasource_read = {
    "Read": "Allow",
    "Connect": "Allow",
    "ExportXml": "Deny",
    "Write": "Deny",
    "SaveAs": "Deny",
    "VizqlDataApiAccess": "Deny",
    "PulseMetricDefine": "Deny",
    "ChangeHierarchy": "Deny",
    "Delete": "Deny",
    "ChangePermissions": "Deny",
    "ExtractRefresh": "Allow",
}

datasource_write = {
    "Read": "Allow",
    "Connect": "Allow",
    "ExportXml": "Allow",
    "Write": "Allow",
    "SaveAs": "Allow",
    "VizqlDataApiAccess": "Allow",
    "PulseMetricDefine": "Allow",
    "ChangeHierarchy": "Deny",
    "Delete": "Deny",
    "ChangePermissions": "Deny",
    "ExtractRefresh": "Allow",
}

flow_deny_all = {"Read": "Deny",
            "ExportXml": "Deny",
            "Execute": "Deny",
            "Write": "Deny",
            "WebAuthoringForFlows": "Deny",
            "ChangeHierarchy": "Deny",
            "Delete": "Deny",
            "ChangePermissions": "Deny"
            }

flow_none_all = {"Read": None,
            "ExportXml": None,
            "Execute": None,
            "Write": None,
            "WebAuthoringForFlows": None,
            "ChangeHierarchy": None,
            "Delete": None,
            "ChangePermissions": None
            }

flow_read = {"Read": "Allow",
            "ExportXml": "Deny",
            "Execute": "Deny",
            "Write": "Deny",
            "WebAuthoringForFlows": "Deny",
            "ChangeHierarchy": "Deny",
            "Delete": "Deny",
            "ChangePermissions": "Deny"
            }

flow_write = {"Read": "Allow",
            "ExportXml": "Deny",
            "Execute": "Allow",
            "Write": "Allow",
            "WebAuthoringForFlows": "Allow",
            "ChangeHierarchy": "Deny",
            "Delete": "Deny",
            "ChangePermissions": "Deny"
            }

metric_deny_all = {"Read": "Deny",
                  "Write": "Deny",
                  "ChangeHierarchy": "Deny",
                  "Delete": "Deny",
                  "ChangePermissions": "Deny"
                  }

metric_none_all = {"Read": None,
                  "Write": None,
                  "ChangeHierarchy": None,
                  "Delete": None,
                  "ChangePermissions": None
                  }

metric_read = {"Read": "Allow",
              "Write": "Deny",
              "ChangeHierarchy": "Deny",
              "Delete": "Deny",
              "ChangePermissions": "Deny"
              }

metric_write = {"Read": "Allow",
               "Write": "Allow",
               "ChangeHierarchy": "Deny",
               "Delete": "Deny",
               "ChangePermissions": "Deny"
               }
