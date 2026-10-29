from odoo import api, SUPERUSER_ID

VIEW_XMLID_NAME = 'documents_document_list_activity_column'


def post_init_hook(env):
    """Find the main list view of documents.document (whatever its XML id is
    in this database) and add the Activities column to it."""
    View = env['ir.ui.view']
    parent = View.search([
        ('model', '=', 'documents.document'),
        ('type', '=', 'list'),
        ('inherit_id', '=', False),
    ], order='priority, id', limit=1)
    if not parent:
        return

    if "name=\"write_date\"" in (parent.arch_db or '') or "name='write_date'" in (parent.arch_db or ''):
        arch = """
            <xpath expr="//field[@name='write_date']" position="before">
                <field name="activity_ids" widget="list_activity" optional="show"/>
            </xpath>"""
    else:
        arch = """
            <xpath expr="//list" position="inside">
                <field name="activity_ids" widget="list_activity" optional="show"/>
            </xpath>"""

    view = View.create({
        'name': 'documents.document.list.activity.column',
        'model': 'documents.document',
        'inherit_id': parent.id,
        'mode': 'extension',
        'arch_base': '<data>%s</data>' % arch,
    })
    env['ir.model.data'].create({
        'name': VIEW_XMLID_NAME,
        'module': 'documents_activity_column',
        'model': 'ir.ui.view',
        'res_id': view.id,
        'noupdate': True,
    })
