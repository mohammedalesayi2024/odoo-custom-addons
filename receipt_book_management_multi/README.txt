Receipt Book Management - Multiple Books
==============================================

Extension module for the original Odoo 19 module:
receipt_book_management

Install this module AFTER the original module.

It does not duplicate the original models, menus, security groups, views,
or XML IDs. It extends the existing receipt.book and account.payment models.

Behavior:
- A salesperson can have multiple non-finished receipt books.
- Number ranges for the same salesperson/company cannot overlap.
- On customer payments, the user can select the receipt book.
- Posting uses the selected receipt book's next number.
