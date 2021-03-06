from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardPrenda(models.TransientModel):
    _name = 'motgama.wizardprenda'
    _description = 'Recaudo de prenda'

    valor = fields.Float(string='Saldo total',readonly=True,default=lambda self: self._get_valor())
    deuda = fields.Float(string='Saldo restante',compute='_compute_deuda')
    factura = fields.Many2one(string="Factura",comodel_name='account.invoice',default=lambda self: self._get_factura())
    prenda = fields.Many2one(string='Prenda',comodel_name='motgama.prendas',default=lambda self: self._get_prenda())
    pagos = fields.Many2many(string='Recaudo',comodel_name='motgama.wizardpago')

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
    
    @api.depends('pagos.valor')
    def _compute_deuda(self):
        for record in self:
            deuda = record.valor
            for pago in record.pagos:
                deuda -= pago.valor
            record.deuda = deuda

    @api.multi
    def recaudar(self):
        self.ensure_one()
        if abs(self.deuda) >= 0.01:
            raise Warning('La cuenta no ha sido saldada')
        elif self.deuda < 0:
            raise Warning('El valor pagado es mayor al valor de la cuenta')

        valoresRecaudo = {
            'movimiento_id': self.factura.recaudo.movimiento_id.id,
            'habitacion': self.factura.habitacion_id.id,
            'cliente': self.prenda.cliente_id.id,
            'factura': self.factura.id,
            'total_pagado': self.valor,
            'valor_pagado': self.valor,
            'tipo_recaudo': 'prenda',
            'recepcion_id': self.env.user.recepcion_id.id
        }
        recaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not recaudo:
            raise Warning('No fue posible guardar el recaudo')

        for pago in self.pagos:
            valoresPayment = {
                'amount': pago.valor,
                'currency_id': pago.mediopago.diario_id.company_id.currency_id.id,
                'invoice_ids': [(4,self.factura.id)],
                'journal_id': pago.mediopago.diario_id.id,
                'payment_date': fields.Datetime().now(),
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'partner_type': 'customer',
                'partner_id': self.prenda.cliente_id.id
            }
            payment = self.env['account.payment'].sudo().create(valoresPayment)
            if not payment:
                raise Warning('No fue posible sentar el registro del pago')
            payment.sudo().post()

            valoresPago = {
                'cliente_id': self.prenda.cliente_id.id,
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'recaudo': recaudo.id,
                'pago_id': payment.sudo().id
            }
            pago = self.env['motgama.pago'].create(valoresPago)
            if not pago:
                raise Warning('Error al asentar el pago de la prenda')

        valoresPrenda = {
            'pagado': True,
            'pagadofecha': fields.Datetime().now(),
            'pago_uid': self.env.user.id,
            'recaudo': recaudo.id,
            'active': False
        }
        guardado = self.prenda.write(valoresPrenda)
        if not guardado:
            raise Warning('Error al asentar el pago de la prenda')

        return True