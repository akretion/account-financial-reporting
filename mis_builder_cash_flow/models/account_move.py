from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # same as amount_residual but including other internal_type
    # for advance in and out payments
    amount_residual_extended = fields.Monetary(
        string='Amount Due', store=True,
        compute='_compute_amount_residual_extended'
    )

    @api.depends("line_ids.full_reconcile_id")
    def _compute_amount_residual_extended(self):
        for move in self:
            total_party_residual = 0
            total_bank_residual = 0
            for aml in move.line_ids:
                if aml.account_id.internal_type in ('receivable', 'payable'):
                    total_party_residual += aml.amount_residual   # TODO currency?
            for aml in move.line_ids:
                if aml.account_id.internal_type in ('other',):
                    if total_party_residual > 0.01 and aml.full_reconcile_id:
                        # party is not reconciled but bank transfer is
                        total_party_residual = 0
#                        total_bank_residual += aml.amount_residual   # TODO currency?
#                        total_bank_residual -= abs(aml.balance)
#                    else:

            move.amount_residual_extended = total_party_residual + total_bank_residual
