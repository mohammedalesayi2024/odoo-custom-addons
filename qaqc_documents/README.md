# QA/QC Documents Management — Odoo 19

Version: 19.0.2.0.0

## Included document types
- PRQ — Pre-Qualification
- MAR — Material Approval Request
- MES — Method Statement with ITP, ICL and Risk Assessment registers
- MIR — Material Inspection Request, linked to an approved MAR
- RSN — Request Start New with parallel discipline clearances
- WIR — Work Inspection Request; successful A/B consultant outcome schedules a Commercial follow-up activity
- NCR — Non-Conformance Report with optional WIR link and corrective/preventive action closure

## Approval workflow
1. A user creates a document and uploads supporting files.
2. Submit moves the document to **Pending QA/QC**.
3. Only users in **QA/QC: QA/QC Reviewer** can approve or reject the internal review. A QA/QC rejection requires review comments and does not forward the document.
4. QA/QC approval moves the document directly to **Pending Consultant**. There is no Document Control approval stage.
5. Only users in **QA/QC: Consultant** can select:
   - A — Approved
   - B — Approved as Noted
   - C — Revise & Resubmit (comments required; revision counter increases and a revision log is created)
   - D — Rejected
6. On C, the document returns to the submitter for changes and must pass QA/QC again before another Consultant decision.

## Chatter and files
- The Attachments tab uses Odoo attachments and posts newly added files to the document chatter.
- Binary supporting fields (where provided on PRQ/MAR) are linked as field attachments and posted to chatter when uploaded/updated.
- Chatter followers are added for the QA/QC reviewer group on submission and Consultant group after QA/QC approval. Access to the document itself still follows Odoo model access rules.

## Project-specific supplier approval
PRQ A or B Consultant approval registers the supplier as approved for that project. MAR validation checks this project-specific approved-vendor record; it no longer relies on the legacy global partner flag.

## Installation
1. Back up the database and filestore.
2. Copy the `qaqc_documents` folder into an addons path.
3. Restart Odoo and update the Apps list.
4. Install **QA/QC Documents Management**.
5. Assign users to the QA/QC groups under Settings → Users & Companies → Users.
6. Configure project header fields (Project Code, Project No., Contractor Code, Employer, Engineer, Contractor) on each project.

## Important validation note
This package has passed Python syntax compilation and XML well-formedness checks in the build environment. It has **not** been installed against a running Odoo 19 server or exercised in a live database in this environment. Perform the acceptance tests below on a staging database before production deployment.

## Minimum acceptance tests
- Procurement user creates PRQ, uploads files, submits; files appear in chatter.
- QA/QC reviewer sees PRQ in Pending QA/QC and can approve/reject; rejection requires comments and does not expose Consultant decision buttons.
- After QA/QC approval, Consultant group sees the document and only then can choose A/B/C/D.
- B/C/D require Consultant comments; C increments revision, creates a revision-history entry and requires resubmission through QA/QC.
- A/B on PRQ adds supplier to the approved supplier list for that project only.
- MAR cannot use a supplier without an approved PRQ in the same project.
- MIR cannot link to MAR unless its Consultant outcome is A or B.
- WIR A/B creates a Commercial follow-up activity.
- NCR can link optionally to WIR and cannot be closed without corrective action by QA/QC.
- Confirm chatter attachment visibility for the actual Consultant user and verify document access rules for the company's security policy.
