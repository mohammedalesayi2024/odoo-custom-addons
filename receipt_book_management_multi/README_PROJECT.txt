Receipt Book Management (Odoo 17)

Models
-------
receipt.book
receipt.exception
account.payment (inherit)

Receipt Book Fields
-------------------
- Salesperson
- From Receipt No
- To Receipt No
- Next Receipt No
- Total Receipts
- Remaining Receipts
- State
- Issue Date
- Notes

Receipt Exception Fields
------------------------
- Salesperson
- Receipt No
- Status (Lost / Damaged / Cancelled)
- Notes

Rules
-----
- One Active receipt book per salesperson.
- No overlapping ranges for the same salesperson.
- Remaining = Total - Used - Exceptions.
- Warning when remaining <= 10.
- Finished when remaining = 0.


This folder is receipt_book_management_multi, an extension of receipt_book_management. It intentionally depends on the original module so existing receipt.book and account.payment data remain shared. The original module files are retained for completeness but are not imported/loaded by this extension.
