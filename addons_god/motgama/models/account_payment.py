from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    genera_recaudo = fields.Boolean(string="Genera recaudo",default=False)
    mediopago_id = fields.Many2one(string="Medio de pago",comodel_name="motgama.mediopago",domain=[('tipo','not in',['prenda','abono'])])

    @api.onchange('mediopago_id')
    def _onchange_mediopago(self):
        if self.mediopago_id:
            self.journal_id = self.mediopago_id.diario_id.id

    @api.multi
    def action_validate_invoice_payment(self):
        self.ensure_one()
        
        if self.genera_recaudo:
            valores_pago = {
                'movimiento_id': self.invoice_ids[0].movimiento_id.id if self.invoice_ids[0].movimiento_id else False,
                'cliente_id': self.partner_id.id,
                'mediopago': self.mediopago_id.id,
                'valor': self.amount,
                'pago_id': self.id
            }
            pago = self.env['motgama.pago'].create(valores_pago)
            valores_recaudo = {
                'movimiento_id': valores_pago['movimiento_id'],
                'habitacion': self.invoice_ids[0].habitacion_id.id if self.invoice_ids[0].habitacion_id else False,
                'cliente': self.partner_id.id,
                'factura': self.invoice_ids[0].id,
                'total_pagado': self.amount,
                'valor_pagado': self.amount,
                'tipo_recaudo': 'otros',
                'recepcion_id': self.env.user.recepcion_id.id,
                'pagos': [(6,0,[pago.id])]
            }
            recaudo = self.env['motgama.recaudo'].create(valores_recaudo)
            self.invoice_ids[0].sudo().write({'recaudo': recaudo.id})
        return super().action_validate_invoice_payment()