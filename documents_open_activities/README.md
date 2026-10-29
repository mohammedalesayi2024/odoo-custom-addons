# Documents Open Activities Column (Odoo 19)

## What it does
Adds an **Activity** column to the Documents list. For each document, it displays
open activities linked to that document, including activity type, summary (if any),
assigned user, and deadline. Completed activities are not shown because Odoo removes
scheduled activities from `mail.activity` when they are marked done.

## Install
1. Copy `documents_open_activities` into your custom addons directory.
2. Restart/update the Odoo app list.
3. Install **Documents Open Activities Column** from Apps.
4. Open Documents and enable/show the **Activity** column if needed.

## Notes
- Intended for Odoo 19.
- The view inherits `documents.document_view_list`. If your Odoo 19 database uses a
  different external ID for the Documents list view, adjust `inherit_id` accordingly.
- The column is read-only. It does not change the existing activity workflow or access
  rights.
