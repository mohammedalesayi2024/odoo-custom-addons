# QA/QC Documents - PRQ Workflow (Odoo 19)

## What it provides
- PRQ supplier pre-qualification request with required project, supplier and scope.
- Configurable approval workflows: general or project-specific, ordered steps, user/group assignees.
- Approval history with decision, responsible user, timestamp and comments.
- Workflow actions: submit, start review, approve step, return for changes, reject, cancel and manager reset.
- Supplier QA/QC approved flag after final approval.
- Menu under the Odoo Documents app and optional linking of supporting attachments into a Documents folder named `QA/QC PRQ`.

## Dependencies
Odoo 19 Enterprise/installation with `documents`, plus `project`, `contacts`, `mail` and `base`.

## Installation
1. Copy `qaqc_prq_odoo19` into a directory in `addons_path`.
2. Restart Odoo and update the Apps list.
3. Install **QA/QC Documents - PRQ Workflow**.
4. Assign users to the QA/QC PRQ User, Reviewer and Manager groups.
5. In Documents, create a folder named `QA/QC PRQ` if supporting files should also appear there.
6. Open Documents → QA/QC → Configuration → PRQ Approval Workflows.
7. Create an active workflow and add at least one step. Each step must have a specific user or responsible group.
8. Create a PRQ, attach at least one supporting document, then submit.

## Workflow behavior
- Project-specific workflow takes precedence over the general workflow.
- Only the current assigned user/group (or QA/QC manager/system administrator) can decide a step.
- Final supplier approval happens only after all required steps are complete.
- Returning for changes increments the revision and preserves previous decision history. Resubmission starts a new approval run.
- Rejection requires a reason.

## Important implementation notes
- The `res.partner.qaqc_approved_vendor` flag is a general supplier flag for compatibility. If a supplier can be approved in one project but not another, use the PRQ records as the authoritative project-specific qualification status; do not rely on the global flag alone.
- Documents attachment linking expects a folder named `QA/QC PRQ`. If no such folder exists, PRQ attachments remain stored on the PRQ record and are not copied into Documents.
- Review the XML IDs and field compatibility against your exact Odoo 19 build in a staging database before production deployment. This archive has not been installed against a live Odoo server in this environment.
