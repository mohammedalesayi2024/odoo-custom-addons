{
    "name": "Documents Open Activities Column",
    "version": "19.0.1.0.0",
    "category": "Productivity/Documents",
    "summary": "Show open activities and assigned users in the Documents list",
    "description": """
Adds an Activity column to the Documents list showing each open activity,
its type/summary, assigned user, and deadline.
""",
    "license": "LGPL-3",
    "depends": ["documents", "mail"],
    "data": [
        "views/documents_document_views.xml",
    ],
    "installable": True,
    "application": False,
}
