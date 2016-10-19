# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
#   @author Joel Grand-Guillaume and Vincent Renaville
# © 2016-Today Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Export CSV',
    'version': '9.0.1.0.0',
    'depends': [
        'account',
    ],
    'author': "Camptocamp, Akretion, Odoo Community Association (OCA)",
    'description': """

    Add a wizard that allow you to export a csv file based on accounting
    journal entries

    - Trial Balance
    - Analytic Balance (with accounts)
    - Journal Entries

    You can filter by period

    TODO: rearange wizard view with only one button to generate file plus
    define a selection list to select report type
    """,
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'data': [
        'wizard/account_export_csv_view.xml',
        'views/menu.xml',
    ],
    'installable': False,
    'active': False,
}
