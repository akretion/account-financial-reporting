# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class LedgerReportWizard(models.TransientModel):

    _name = "ledger.report.wizard"
    _description = "Ledger Report"

    company_id = fields.Many2one(comodel_name='res.company')
    # date_range = ??
    date_from = fields.Date()
    date_to = fields.Date()
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves',
                                   required=True,
                                   default='posted')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Filter accounts',
    )
    amount_currency = fields.Boolean(string='With currency',
                                     default=False)
    centralize = fields.Boolean(string='Activate centralization',
                                default=False)
    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')
         ],
        string="Partner's",
        default='customer')
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Filter partners',
    )

    @api.multi
    def check_report(self):
        return True