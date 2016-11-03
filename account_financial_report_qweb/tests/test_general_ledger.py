# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from . import abstract_test
from openerp.tests.common import TransactionCase


class TestGeneralLedger(abstract_test.AbstractTest):
    """
        Technical tests for General Ledger Report.
    """

    def _getReportModel(self):
        return self.env['report_general_ledger_qweb']

    def _getQwebReportName(self):
        return 'account_financial_report_qweb.report_general_ledger_qweb'

    def _getXlsxReportName(self):
        return 'account_financial_report_qweb.report_general_ledger_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report_qweb.' \
               'action_report_general_ledger_xlsx'

    def _getReportTitle(self):
        return 'General Ledger'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.env.ref('base.main_company').id,
            'fy_start_date': time.strftime('%Y-01-01'),
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_balance_at_0': True},
            {'centralize': True},
            {'only_posted_moves': True, 'hide_account_balance_at_0': True},
            {'only_posted_moves': True, 'centralize': True},
            {'hide_account_balance_at_0': True, 'centralize': True},
            {
                'only_posted_moves': True,
                'hide_account_balance_at_0': True,
                'centralize': True
            },
        ]


class TestGeneralLedgerReport(TransactionCase):


    def _add_reversale_move(self):
        move_name = 'expense accrual'
        partner = self.env.ref('base.res_partner_12')
        journal = self.env['account.journal'].search([
            ('code', '=', 'MISC')])
        partner = self.env.ref('base.res_partner_12')
        move_vals = {
            'journal_id': journal.id,
            'partner_id': partner.id,
            'name': move_name,
            'date': self.previous_fy_date_end,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': 1000,
                    'account_id': self.receivable_account.id}),
                (0, 0, {
                    'name': move_name,
                    'credit': 1000,
                    'account_id': self.income_account.id}),
                ]}
        self.env['account.move'].create(move_vals)

        move_vals['date'] = self.fy_date_end
        move_vals['line_ids'][0][2].update({
            'credit': 1000,
            'debit': 0,
            })
        move_vals['line_ids'][1][2].update({
            'credit': 0,
            'debit': 1000,
            })
        move = self.env['account.move'].create(move_vals)
        move.post()

    def _get_report_line_for_receivable_account(self):
        company = self.env.ref('base.main_company')
        general_ledger = self.env['report_general_ledger_qweb'].create({
            'date_from': self.fy_date_start,
            'date_to': self.fy_date_end,
            'only_posted_moves': True,
            'hide_account_balance_at_0': True,
            'company_id': company.id,
            'fy_start_date': self.fy_date_start,
            })
        general_ledger.compute_data_for_report(
            with_line_details=False, with_partners=False
        )
        line = self.env['report_general_ledger_qweb_account'].search([
            ('report_id', '=', general_ledger.id),
            ('account_id', '=', self.receivable_account.id),
            ])
        return line

    def test_init_balance(self):
        self.previous_fy_date_end = '2015-12-31'
        self.fy_date_start = '2016-01-01'
        self.fy_date_end = '2016-12-31'
        self.receivable_account = self.env['account.account'].search([
            ('user_type_id.name', '=', 'Receivable')
            ], limit=1)
        self.income_account = self.env['account.account'].search([
            ('user_type_id.name', '=', 'Income')
            ], limit=1)

        # Generate the general ledger line
        line = self._get_report_line_for_receivable_account()
        initial_credit = line.initial_credit
        initial_debit = line.initial_debit
        # Add a reversale move to add + 1000 to the initial_credit
        self._add_reversale_move()
        # Re Generate the general ledger line
        new_line = self._get_report_line_for_receivable_account()
        self.assertEqual(new_line.initial_credit,line.initial_credit + 1000)
        self.assertEqual(new_line.initial_debit, line.initial_debit)
