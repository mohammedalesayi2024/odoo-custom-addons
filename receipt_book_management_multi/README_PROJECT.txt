Receipt Book Management - Multiple Books (Odoo 19)

Standalone module. It does NOT depend on or inherit from the original receipt_book_management module.

It uses its own receipt-book models, exception models, wizard models, menus, security group, XML IDs, and unique fields on account.payment so it can coexist with the original module.

The same salesperson may have multiple active receipt books as long as their receipt-number ranges do not overlap.
