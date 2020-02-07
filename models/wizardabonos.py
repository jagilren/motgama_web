from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaWizardAbonos(models.TransientModel):
    _name = 'motgama.wizard.abonos'
    _description = 'Wizard Abonos'

    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',default=lambda self: self._get_movimiento())
    saldo = fields.Float(string='Saldo habitación',compute='_compute_saldo')
    abonado = fields.Float(string='Nuevo abono',compute='_compute_abonado')
    abonos = fields.Float(string='Abonado anteriormente',readonly=True,default=lambda self: self._get_abonos())
    pagos = fields.Many2many(string='Pagos',comodel_name='motgama.wizardpago')

    @api.model
    def _get_movimiento(self):
        flujo = self.env.context['active_id']
        flujo_id = self.env['motgama.flujohabitacion'].search([('id','=',flujo)],limit=1)
        return flujo_id.ultmovimiento.id

    @api.model
    def _get_abonos(self):
        flujo = self.env.context['active_id']
        flujo_id = self.env['motgama.flujohabitacion'].search([('id','=',flujo)],limit=1)
        abonado = 0.0
        for recaudo in flujo_id.ultmovimiento.recaudo_ids:
            abonado += recaudo.total_pagado
        return abonado

    @api.depends('abonos','pagos.valor')
    def _compute_saldo(self):
        for record in self:
            saldo = record.abonos
            for pago in record.pagos:
                saldo += pago.valor
            record.saldo = saldo

    @api.depends('pagos.valor')
    def _compute_abonado(self):
        for record in self:
            abonado = 0.0
            for pago in record.pagos:
                abonado += pago.valor
            record.abonado = abonado

    @api.multi
    def recaudar(self):
        self.ensure_one()

        if self.abonado == 0:
            raise Warning('No se abonó ningún valor')

        valoresPagos = []
        for pago in self.pagos:
            if pago.valor <= 0:
                raise Warning('El valor del pago no puede ser menor o igual a cero')
            valoresPayment = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'amount': pago.valor,
                'journal_id': pago.mediopago.diario_id.id,
                'payment_date': fields.Date().today(),
                'payment_method_id': 1,
                'communication': 'Abono para movimiento con id: ' + str(self.movimiento_id.id)
            }
            payment = self.env['account.payment'].create(valoresPayment)
            if not payment:
                raise Warning('No se pudo registrar el pago')
            payment.post()
            
            valores = {
                'cliente_id': self.env.ref('motgama.cliente_contado').id,
                'fecha': fields.Datetime().now(),
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'usuario_uid': self.env.user.id,
                'pago_id': payment.id
            }
            valoresPagos.append(valores)
        
        valoresRecaudo = {
            'movimiento_id': self.movimiento_id.id,
            'total_pagado': self.abonado,
            'valor_pagado': self.abonado,
            'usuario_uid': self.env.user.id,
        }
        recaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not recaudo:
            raise Warning('No se pudo registrar el recaudo')

        for valoresPago in valoresPagos:
            valoresPago.update({'recaudo':recaudo.id})
            pago = self.env['motgama.pago'].create(valoresPago)
            if not pago:
                raise Warning('No se pudo registrar el pago')
        
        return True

class MotgamaAbonos(models.TransientModel):
    _name = 'motgama.abonos'
    _description = 'Ver Abonos'

    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',default=lambda self: self._get_movimiento())
    abono_ids = fields.Many2many(string='Abonos',comodel_name='motgama.recaudo',compute='_compute_abonos')
    saldo = fields.Float(string='Saldo',compute='_compute_saldo')

    @api.model
    def _get_habitacion(self):
        flujo = self.env.context['active_id']
        return self.env['motgama.flujohabitacion'].search([('id','=',flujo)],limit=1).id

    @api.model
    def _get_movimiento(self):
        flujo = self.env.context['active_id']
        return self.env['motgama.flujohabitacion'].search([('id','=',flujo)],limit=1).ultmovimiento.id

    @api.depends('movimiento_id')
    def _compute_abonos(self):
        for record in self:
            if record.movimiento_id:
                ids = [recaudo.id for recaudo in record.movimiento_id.recaudo_ids]
                record.abono_ids = [(6,0,ids)]
    
    @api.depends('abono_ids.valor_pagado')
    def _compute_saldo(self):
        for record in self:
            saldo = 0.0
            for abono in record.abono_ids:
                saldo += abono.valor_pagado
            record.saldo = saldo
    
class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def abonos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.abonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Abonos de la habitación ' + self.codigo
        }

    @api.multi
    def abonar(self):
        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.abonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }