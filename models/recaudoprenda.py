from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaPrendas(models.Model):
    _inherit = 'motgama.prendas'

    @api.multi
    def recaudo_prenda(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardprenda',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('motgama.form_wizard_prenda').id,
            'target': 'new'
        }

class MotgamaWizardPrenda(models.TransientModel):
    _name = 'motgama.wizardprenda'
    _description = 'Recaudo de prenda'

    mediopago = fields.Many2one(string='Medio de pago',comodel_name='motgama.mediopago')
    valor = fields.Float(string='Valor a pagar',readonly=True,default=lambda self: self._get_valor())
    pagado = fields.Selection(string='He recibido la totalidad del pago de la prenda',selection=[('S','Sí')],required=True)
    factura = fields.Many2one(string="Factura",comodel_name='account.invoice',default=lambda self: self._get_factura())
    prenda = fields.Many2one(string='Prenda',comodel_name='motgama.prendas',default=lambda self: self._get_prenda())

    @api.model
    def _get_prenda(self):
        idPrenda = self.env.context['active_id']
        return self.env['motgama.prendas'].search([('id','=',idPrenda)],limit=1).id

    @api.model
    def _get_factura(self):
        idPrenda = self.env.context['active_id']
        prenda = self.env['motgama.prendas'].search([('id','=',idPrenda)],limit=1)
        if not prenda:
            raise Warning('Error del sistema: no se encuentra el registro de prenda')
        return prenda.factura.id

    @api.model
    def _get_valor(self):
        idPrenda = self.env.context['active_id']
        prenda = self.env['motgama.prendas'].search([('id','=',idPrenda)],limit=1)
        if not prenda:
            raise Warning('Error del sistema: no se encuentra el registro de prenda')
        return prenda.valordeuda

    @api.multi
    def recaudar(self):
        self.ensure_one()
        diario = self.env['account.journal'].search([('company_id','=',self.factura.company_id.id),('type','=','cash')],limit=1)
        valorPagado = self.valor
        valoresPayment = {
            'amount': valorPagado,
            'currency_id': self.mediopago.diario_id.company_id.currency_id.id,
            'invoice_ids': [(4,self.factura.id)],
            'journal_id': self.mediopago.diario_id.id,
            'payment_date': fields.Datetime().now(),
            'payment_type': 'inbound',
            'payment_method_id': 1,
            'partner_type': 'customer'
        }
        payment = self.env['account.payment'].create(valoresPayment)
        if not payment:
            raise Warning('No fue posible sentar el registro del pago')
        payment.post()

        valoresPago = {
            'cliente_id': self.prenda.cliente_id.id,
            'mediopago': self.mediopago.id,
            'valor': self.valor,
            'recaudo': self.factura.recaudo.id
        }
        pago = self.env['motgama.pago'].create(valoresPago)
        if not pago:
            raise Warning('Error al asentar el pago de la prenda')

        pagado = self.factura.recaudo.valor_pagado + self.valor
        self.factura.recaudo.write({'valor_pagado': pagado})

        valoresPrenda = {
            'pagado': True,
            'pagadofecha': fields.Datetime().now(),
            'pagadoforma': self.mediopago.id,
            'pago_uid': self.env.user.id,
            'active': False
        }
        guardado = self.prenda.write(valoresPrenda)
        if not guardado:
            raise Warning('Error al asentar el pago de la prenda')

        return True