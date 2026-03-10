"""
The top level projects to have in Tableau Online. Project = Folder.
We lock permissions to the top level folder and all subfolders will inherit the same permissions.
"""

top_level_projects = {
    # Tableau Created Projects
    # "default": """""",
    "Samples": """Contains samples for using Tableau with fake data from other sources""",
    "Admin Insights": """Datasources and workbooks for understanding Tableau use. The datasources are created by
     Tableau""",
    # Company Created Projects
    "Company All": """Datasources and workbooks for everyone who works at Company to use.""",
    "Finance": """Datasources and workbooks for the Finance team. Data sources in this project will be restricted to
    the Finance and Executive teams.""",
    "Marketing": """Datasources and workbooks for the Marketing team. Data sources in this project will be restricted
    to the Marketing and Executive teams.""",
    "Customer Success": """Datasources and workbooks for the Customer Success team. Data sources in this project will
    be restricted to the Customer Success and Executive teams.""",
    "Product": """Datasources and workbooks for the Product team. Data sources in this project will be restricted to
        the Product, Engineering, and Executive teams.""",
    "Engineering": """Datasources and workbooks for the Engineering team. Data sources in this project will be
    restricted to the Product, Engineering, and Executive teams.""",
    "Sales": """Datasources and workbooks for the Sales team. Data sources in this project will be
    restricted to the Security Team.""",
    "Security": """Datasources and workbooks for the Security team. Data sources in this project will be
        restricted to the Security Team.""",
    "People": """Datasources and workbooks for the People team. Data sources in this project will be restricted to the
        People and Executive teams.""",
    "Recruiting": """Datasources and workbooks for the Recruiting team. Data sources in this project will be restricted
        to the Recruiting and Executive teams.""",
    "IT": """Datasources and workbooks for the IT team. Data sources in this project will be restricted to the IT and
        Executive teams.""",
    "Executive": """Datasources and workbooks for the Executive Team. Data sources in this project will be restricted
        to the Executive Team.""",
    "Strategy & Operations": """Datasources and workbooks for the Strategy & Operations Team. Data sources in this
        project will be restricted to the Strategy & Operations Team.""",
    "Sales Managers": """Datasources and workbooks for sales managers. Data sources in this project will be
        restricted to the Sales Management team.""",
}

