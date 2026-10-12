# Salesperson Portal Access (Odoo 19 Community)

This module adjusts the salesperson selector on contacts (`res.partner`) so active portal users can be selected alongside internal users.

## Install
1. Extract `salesperson_portal_access` into your `custom_addons` folder.
2. Restart the Odoo container:
   `docker compose up -d --force-recreate web`
3. In Odoo, enable Developer Mode, open Apps, click **Update Apps List**, and search for **Salesperson Portal Access**.
4. Install the module.

## Notes
- This changes the selector's domain only; it does not grant portal users internal access rights.
- Portal users may not have access to all features that expect an internal salesperson. Test with a non-production database first.
- The XML inherits the standard partner form view and updates the `user_id` field domain. If the view fails to install because the field/view structure differs in your Odoo build, check the server log and adapt the XPath to the actual inherited view.
