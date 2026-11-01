# Bank Smart Scanner – Odoo 19 Enterprise

Custom Odoo 19 module for importing bank statement files and preparing draft journal entries.

## Included in this build
- Multi-bank import profiles with per-profile CSV/XLSX column mapping.
- Import sessions and transaction review models.
- CSV and XLSX import (requires `openpyxl` on the Odoo server for XLSX).
- Basic text-based PDF extraction (requires `pypdf` on the Odoo server).
- Strict partner matching by exact bank account number/IBAN or exact partner reference.
- Potential duplicate detection.
- Draft `account.move` generation and explicit posting action restricted to scanner managers.
- Company record rules and accounting roles.

## Important limitations of this initial build
- OCR for image-only/scanned PDFs is not included. It requires a separately installed OCR engine/service and bank-specific extraction profiles.
- PDF table parsing is generic and cannot guarantee correct extraction from every bank layout. Validate a real statement and configure a parser/profile for each bank before production use.
- The current implementation creates journal entries, not `account.payment` records. Posting a receivable/payable journal entry does not automatically register a payment or reconcile an invoice. Reconciliation remains a separate accounting operation.
- The first version creates draft entries per approved transaction. List-level multi-record actions are provided, but batch posting is processed record-by-record and is not an all-or-nothing atomic batch.
- Bank statement opening/closing balance reconciliation and bank-specific PDF profile mapping are not yet implemented.

## Server dependencies
- `openpyxl` for XLSX import.
- `pypdf` for text-based PDF extraction.

Install these packages in the Odoo server environment where permitted by the hosting provider. Odoo.sh deployments may require adding dependencies through the repository's requirements configuration and checking platform support.

## Installation
1. Copy `bank_smart_scanner` into the custom addons path.
2. Install the Python dependencies required for the formats you intend to use.
3. Restart Odoo and update the Apps list.
4. Install **Bank Smart Scanner**.
5. Assign Bank Scanner User or Bank Scanner Manager groups.
6. Create a Bank Import Profile and select a bank journal with a configured default account.
7. Test with sanitized sample statements before production use.

## Validation performed on the package
- Python syntax compilation.
- XML well-formedness parsing.
- ZIP archive integrity.

These checks do not replace installation and functional testing on an actual Odoo 19 Enterprise database.
