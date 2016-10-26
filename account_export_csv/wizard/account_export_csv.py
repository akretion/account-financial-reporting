# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
#   @author Joel Grand-Guillaume and Vincent Renaville
#    CSV data formating inspired from
# http://docs.python.org/2.7/library/csv.html?highlight=csv#examples
# © 2016-Today Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import itertools
import tempfile
from cStringIO import StringIO
import base64
from datetime import date

import csv
import codecs

from openerp import api, fields, models
from openerp.tools.translate import _


class AccountUnicodeWriter(object):

    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        # created a writer with Excel formating settings

        self.writer = csv.writer(self.queue, dialect=dialect,
                                 quoting=csv.QUOTE_ALL, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        # we ensure that we do not try to encode none or bool
        row = (x or u'' for x in row)

        encoded_row = [
            c.encode("utf-8") if isinstance(c, unicode) else c for c in row]

        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class AccountCSVExport(models.TransientModel):
    _name = 'account.csv.export'
    _description = 'Export Accounting'

    def _get_company_default(self):
        return self.env.user.company_id.id

    def _get_date_from_default(self):
        date_from = self.env.user.company_id.\
            compute_fiscalyear_dates(date.today())['date_from']
        return date_from

    data = fields.Binary('CSV', readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=_get_company_default, invisible=True)
    date_from = fields.Date(
        'Star Date',
        default=_get_date_from_default,
        help='Date of the beging of the fiscal year if empty')
    date_to = fields.Date(
        'End Date',
        default=fields.Date.context_today,
        help='Date of the end of the fiscal year if empty')
    journal_ids = fields.Many2many(
        'account.journal',
        'rel_wizard_journal',
        'wizard_id',
        'journal_id',
        'Journals',
        help='If empty, use all journals, only used for journal entries')
    account_ids = fields.Many2many(
        'account.account',
        'rel_wizard_account',
        'wizard_id',
        'account_id',
        'Accounts',
        help='If empty, use all accounts, only used for journal entries')
    export_filename = fields.Char(
        'Export CSV Filename', default='account_export.csv', size=128)

    @api.multi
    def action_manual_export_account(self,):
        rows = self.get_data("account")
        file_data = StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.data = base64.encodestring(file_value)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_account(self):
        return [_(u'CODE'),
                _(u'NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_account(
            self, date_from, date_to, journal_ids, account_ids):
        """
        Return list to generate rows of the CSV file
        """
        self._cr.execute("""
                select ac.code,ac.name,
                sum(debit) as sum_debit,
                sum(credit) as sum_credit,
                sum(debit) - sum(credit) as balance
                from account_move_line as aml,account_account as ac
                where aml.account_id = ac.id
                and aml.date >=  %(date_from)s
                and aml.date <=  %(date_to)s         
                and aml.journal_id in %(journal_ids)s
                and aml.account_id in %(account_ids)s
                group by ac.id,ac.code,ac.name
                order by ac.code
                   """,
                   {
                        'date_from': date_from,
                        'date_to': date_to,
                        'journal_ids': tuple(journal_ids),
                        'account_ids': tuple(account_ids),
                    }
                   )
        res = self._cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    @api.multi
    def action_manual_export_analytic(self):
        rows = self.get_data("analytic")
        file_data = StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.data = base64.encodestring(file_value)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_analytic(self):
        return [_(u'ANALYTIC CODE'),
                _(u'ANALYTIC NAME'),
                _(u'CODE'),
                _(u'ACCOUNT NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_analytic(
            self, date_from, date_to, journal_ids, account_ids):
        """
        Return list to generate rows of the CSV file
        """
        self._cr.execute("""  select aac.code as analytic_code,
                        aac.name as analytic_name,
                        ac.code,ac.name,
                        sum(debit) as sum_debit,
                        sum(credit) as sum_credit,
                        sum(debit) - sum(credit) as balance
                        from account_move_line
                        left outer join account_analytic_account as aac
                        on (account_move_line.analytic_account_id = aac.id)
                        inner join account_account as ac
                        on account_move_line.account_id = ac.id
                        and account_move_line.date >=  %(date_from)s
                        and account_move_line.date <=  %(date_to)s 
                        group by aac.id,aac.code,aac.name,ac.id,ac.code,ac.name
                        order by aac.code
                   """,
                   {
                        'date_from': date_from,
                        'date_to': date_to,
                    }
                   )
        res = self._cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows

    @api.multi
    def action_manual_export_journal_entries(self):
        """
        Here we use TemporaryFile to avoid full filling the OpenERP worker
        Memory
        We also write the data to the wizard with SQL query as write seems
        to use too much memory as well.

        Those improvements permitted to improve the export from a 100k line to
        200k lines
        with default `limit_memory_hard = 805306368` (768MB) with more lines,
        you might encounter a MemoryError when trying to download the file even
        if it has been generated.

        To be able to export bigger volume of data, it is advised to set
        limit_memory_hard to 2097152000 (2 GB) to generate the file and let
        OpenERP load it in the wizard when trying to download it.

        Tested with up to a generation of 700k entry lines
        """
        rows = self.get_data("journal_entries")
        with tempfile.TemporaryFile() as file_data:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            with tempfile.TemporaryFile() as base64_data:
                file_data.seek(0)
                base64.encode(file_data, base64_data)
                base64_data.seek(0)
                self._cr.execute("""
                UPDATE account_csv_export
                SET data = %s
                WHERE id = %s""", (base64_data.read(), self.id))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_journal_entries(self):
        return [
            # Standard Sage export fields
            _(u'DATE'),
            _(u'JOURNAL CODE'),
            _(u'ACCOUNT CODE'),
            _(u'PARTNER NAME'),
            _(u'REF'),
            _(u'DESCRIPTION'),
            _(u'DEBIT'),
            _(u'CREDIT'),
            _(u'FULL RECONCILE'),
            #_(u'PARTIAL RECONCILE'),
            _(u'ANALYTIC ACCOUNT CODE'),

            # Other fields
            _(u'ENTRY NUMBER'),
            _(u'ACCOUNT NAME'),
            _(u'BALANCE'),
            _(u'AMOUNT CURRENCY'),
            _(u'CURRENCY'),
            _(u'ANALYTIC ACCOUNT NAME'),
            _(u'JOURNAL'),
            _(u'MONTH'),
            _(u'FISCAL YEAR'),
            _(u'TAX CODE CODE'),
            _(u'TAX CODE NAME'),
            _(u'TAX AMOUNT'),
            _(u'BANK STATEMENT'),
        ]

    def _get_rows_journal_entries(
            self,
            date_from,
            date_to,
            journal_ids,
            account_ids):
        """
        Create a generator of rows of the CSV file
        """
        self._cr.execute("""
        SELECT
          account_move_line.date AS date,
          account_journal.name as journal,
          account_account.code AS account_code,
          res_partner.name AS partner_name,
          account_move_line.ref AS ref,
          account_move_line.name AS description,
          account_move_line.debit AS debit,
          account_move_line.credit AS credit,
          account_full_reconcile.name as full_reconcile,
          -- account_full_reconcile.reconcile_partial_id AS partial_reconcile_id,
          account_analytic_account.code AS analytic_account_code,
          account_move.name AS entry_number,
          account_account.name AS account_name,
          account_move_line.debit - account_move_line.credit AS balance,
          account_move_line.amount_currency AS amount_currency,
          res_currency.name AS currency,
          account_analytic_account.name AS analytic_account_name,
          account_journal.name as journal,
          EXTRACT(MONTH FROM account_move_line.date) AS month,
          EXTRACT(YEAR FROM account_move_line.date) as year,
          account_tax.description AS aml_tax_code_code,
          account_tax.name AS aml_tax_code_name,
          0 AS aml_tax_amount,
          account_bank_statement.name AS bank_statement
        FROM
          public.account_move_line
          JOIN account_account on
            (account_account.id=account_move_line.account_id)
          JOIN account_journal on
            (account_journal.id = account_move_line.journal_id)
          LEFT JOIN res_currency on
            (res_currency.id=account_move_line.currency_id)
          LEFT JOIN account_full_reconcile on
            (account_full_reconcile.id = account_move_line.full_reconcile_id )
          LEFT JOIN res_partner on
            (res_partner.id=account_move_line.partner_id)
          LEFT JOIN account_move on
            (account_move.id=account_move_line.move_id)
          LEFT JOIN account_tax on
            (account_tax.id=account_move_line.tax_line_id)
          LEFT JOIN account_analytic_account on
            (account_analytic_account.id=account_move_line.analytic_account_id)
          LEFT JOIN account_bank_statement on
            (account_bank_statement.id=account_move_line.statement_id)
        WHERE account_move_line.date >=  %(date_from)s
        AND account_move_line.date <=  %(date_to)s 
        AND account_journal.id IN %(journal_ids)s
        AND account_account.id IN %(account_ids)s
        ORDER BY account_move_line.date
        """,
                   {
                       'date_from': date_from,
                       'date_to': date_to,
                       'journal_ids': tuple(journal_ids),
                       'account_ids': tuple(account_ids)}
                   )
        while 1:
            # http://initd.org/psycopg/docs/cursor.html#cursor.fetchmany
            # Set cursor.arraysize to minimize network round trips
            self._cr.arraysize = 100
            rows = self._cr.fetchmany()
            if not rows:
                break
            for row in rows:
                yield row

    def get_data(self, result_type):
        get_header_func = getattr(
            self, ("_get_header_%s" % (result_type)), None)
        get_rows_func = getattr(self, ("_get_rows_%s" % (result_type)), None)
        date_from = None
        date_to = None
        if not self.date_from:
            date_from = self.env.user.company_id.\
                compute_fiscalyear_dates(date.today())['date_from']
        if not self.date_to:
            date_to = self.env.user.company_id.\
                compute_fiscalyear_dates(date.today())['date_to']
        journal_ids = None
        if self.journal_ids:
            journal_ids = self.journal_ids.ids
        else:
            j_obj = self.env["account.journal"]
            journal_ids = j_obj.search([]).ids
        account_ids = None
        if self.account_ids:
            account_ids = self.account_ids.ids
        else:
            aa_obj = self.env["account.account"]
            account_ids = aa_obj.search([]).ids
        rows = itertools.chain(
            (get_header_func(),), get_rows_func(
                date_from,
                date_to,
                journal_ids,
                account_ids,
            )
        )
        return rows
