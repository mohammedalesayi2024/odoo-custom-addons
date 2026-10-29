Odoo 19 Documents Open Activities Column

Adds an Activity column showing open activities, assigned users, and deadlines.

Important: verify the parent view External ID before installation. This version uses
`documents.documents_view_list` as the candidate ID, but your Odoo build may use a
different ID. In Settings > Technical > User Interface > Views, open the Documents
list view and copy its External ID into the `inherit_id` in views/documents_document_views.xml.

Install on a staging branch first. No existing documents or access rights are changed.
