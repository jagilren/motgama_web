from odoo import models, fields, api

class MotgamaWizardAnulaRecaudo(models.TransientModel):
    _name = 'motgama.wizard.anularecaudo'
    _description = 'Wizard Anula Recaudo'

    recaudo_id = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo',default=lambda self: self._get_recaudo())

    @api.model
    def _get_recaudo(self):
        return self.env.context['active_id']
    
    @api.multi
    def anular(self):
        self.ensure_one()

        for pago in self.recaudo_id.pagos:
            pago.pago_id.cancel()
            pago.pago_id.unlink()
        
        self.recaudo_id.sudo().write({'active':False})
        invoice = self.env['account.invoice'].search([('recaudo','=',self.recaudo_id.id)],limit=1)
        if invoice:
            invoice.sudo().write({'recaudo':False})

class MotgamaWizardRecaudoFactura(models.TransientModel):
    _name = 'motgama.wizard.recaudofactura'
    _description = 'Wizard Recaudo de factura'

    factura_id = fields.Many2one(string='Factura',comodel_name='account.invoice',default=lambda self: self._get_factura())
    cliente_id = fields.Many2one(string='Cliente',comodel_name='res.partner',default=lambda self: self._get_cliente)
    total = fields.Float(string='Total',default=lambda self: self._get_total())
    deuda = fields.Float(string='Deuda',compute='_compute_deuda')
    pagos = fields.Many2many(string='Pagos',comodel_name='motgama.wizardpago')
    
    @api.model
    def _get_factura(self):
        return self.env.context['active_id']

    @api.model
    def _get_cliente(self):
        idFac = self.env.context['active_id']
        fac = self.env['account.invoice'].browse(idFac)
        return fac.partner_id.id
    
    @api.model
    def _get_total(self):
        idFac = self.env.context['active_id']
        fac = self.env['account.invoice'].browse(idFac)
        return fac.amount_total

    @api.depends('pagos.valor')
    def _compute_deuda(self):
        for record in self:
            deuda = record.total
            for pago in record.pagos:
                deuda -= pago.valor
            record.deuda = deuda
    
    @api.multi
    def recaudar(self):
        self.ensure_one()

        self.ensure_one()
        if self.deuda >= 0.01:
            raise Warning('La cuenta no ha sido saldada')
        elif self.deuda < 0:
            raise Warning('El valor pagado es mayor al valor de la cuenta')

        valoresPagos = []

        for pago in self.pagos:
            valores = {
                'movimiento_id': self.movimiento.id,
                'cliente_id': self.cliente.id,
                'mediopago': pago.mediopago.id,
                'valor': pago.valor
            }
            if pago.mediopago.tipo in ['prenda','abono']:
                valoresPagos.append(valores)
                continue
            valoresPayment = {
                'amount': pago.valor,
                'currency_id': pago.mediopago.diario_id.company_id.currency_id.id,
                'invoice_ids': [(4,self.factura_id.id)],
                'journal_id': pago.mediopago.diario_id.id,
                'payment_date': fields.Datetime().now(),
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'partner_type': 'customer'
            }
            payment = self.env['account.payment'].create(valoresPayment)
            if not payment:
                raise Warning('No fue posible sentar el registro del pago')
            payment.post()
            valores['pago_id'] = payment.id
            valoresPagos.append(valores)
        
        valoresRecaudo = {
            'cliente': self.cliente_id.id,
            'factura': self.factura_id.id,
            'total_pagado': self.total,
            'valor_pagado': self.total,
            'tipo_recaudo': 'otros',
            'recepcion_id': self.env.user.recepcion_id.id
        }

        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('No se pudo registrar el recaudo')
        self.factura_id.write({'recaudo':nuevoRecaudo.id})

        for valores in valoresPagos:
            valores.update({'recaudo':nuevoRecaudo.id})
            nuevoPago = self.env['motgama.pago'].create(valores)
            if not nuevoPago:
                raise Warning('No se pudo guardar la información del pago')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def recaudo_factura(self):
        self.ensure_one()

        return {
            'name': 'Recaudar factura',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.recaudofactura',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_recaudo_factura').id,
            'target': 'new'
        }

class MotgamaRecaudo(models.Model):
    _inherit = 'motgama.recaudo'

    @api.multi
    def anula_recaudo(self):
        self.ensure_one()

        return {
            'name': 'Anular recaudo',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.anularecaudo',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_anula_recaudo').id,
            'target': 'new'
        }