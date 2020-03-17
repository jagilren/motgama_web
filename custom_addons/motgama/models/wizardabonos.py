from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaWizardAbonos(models.TransientModel):
    _name = 'motgama.wizard.abonos'
    _description = 'Wizard Abonos'

    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',default=lambda self: self._get_movimiento())
    saldo = fields.Float(string='Total abonos realizados',compute='_compute_saldo')
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
        
        hab = self.env['motgama.flujohabitacion'].search([('codigo','=',self.movimiento_id.habitacion_id.codigo)],limit=1)
        if not hab:
            raise Warning('Hay un problema con la habitación')

        valoresRecaudo = {
            'movimiento_id': self.movimiento_id.id,
            'habitacion': hab.id,
            'total_pagado': self.abonado,
            'valor_pagado': self.abonado,
            'usuario_uid': self.env.user.id,
            'tipo_recaudo': 'abonos',
            'recepcion_id': self.env.user.recepcion_id.id
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
    saldo = fields.Float(string='Total abonos realizados',compute='_compute_saldo')

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

class MotgamaRevertirAbonos(models.TransientModel):
    _name = 'motgama.wizard.revertirabonos'
    _description = 'Wizard Revertir Abonos'

    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',readonly=True,default=lambda self: self._get_habitacion())
    abono_ids = fields.Many2many(string='Abonos a revertir',comodel_name='motgama.linearevertirabonos',default=lambda self: self._get_abonos())
    total_abonado = fields.Float(string='Abonado anteriormente',readonly=True, default=lambda self: self._get_abonado())
    total_revertir = fields.Float(string='Total a revertir',compute='_compute_revertir')
    total_abonos = fields.Float(string='Total abonado',compute='_compute_abonos',store=True)

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']
    
    @api.model
    def _get_abonos(self):
        habitacion = self.env['motgama.flujohabitacion'].browse(self.env.context['active_id'])
        array = []
        for recaudo in habitacion.ultmovimiento.recaudo_ids:
            valores = {
                'abono_id': recaudo.id,
                'fecha': recaudo.create_date,
                'valor': recaudo.valor_pagado,
                'revertir': False
            }
            array.append(valores)
        return [(0,0,valores) for valores in array]
    
    @api.model
    def _get_abonado(self):
        habitacion = self.env['motgama.flujohabitacion'].browse(self.env.context['active_id'])
        abonado = 0.0
        for recaudo in habitacion.ultmovimiento.recaudo_ids:
            abonado += recaudo.valor_pagado
        return abonado
    
    @api.depends('abono_ids.revertir')
    def _compute_revertir(self):
        for record in self:
            suma = 0.0
            for abono in record.abono_ids:
                if abono.revertir:
                    suma += abono.valor
            record.total_revertir = suma
    
    @api.depends('total_revertir','total_abonado')
    def _compute_abonos(self):
        for record in self:
            record.total_abonos = record.total_abonado - record.total_revertir

    @api.multi
    def revertir_abonos(self):
        self.ensure_one()
        if self.total_abonos < 0:
            raise Warning('No se pueden revertir abonos ya revertidos')

        for abono in self.abono_ids:
            if abono.revertir:
                revertir = True
                valoresPagos = []
                for pago in abono.abono_id.pagos:
                    if pago.pago_id:
                        asientos = []
                        for apunte in pago.pago_id.move_line_ids:
                            if apunte.move_id.id not in asientos:
                                asientos.append(apunte.move_id.id)
                        self.env['account.move'].browse(asientos).reverse_moves(fields.Date().Today(),asiento.journal_id.id)
                        valores = {
                            'movimiento_id': self.habitacion_id.ultmovimiento.id,
                            'mediopago': pago.mediopago.id,
                            'valor': pago.valor * -1,
                            'fecha': fields.Datetime().now(),
                            'cliente_id': pago.cliente_id.id,
                            'usuario_uid': self.env.user.id,
                        }
                        valoresPagos.append(valores)
                if len(valoresPagos) > 0:
                    valores = {
                        'movimiento_id': self.habitacion_id.ultmovimiento.id,
                        'habitacion': self.habitacion_id.id,
                        'cliente': abono.abono_id.cliente.id,
                        'total_pagado': abono.abono_id.total_pagado * -1,
                        'valor_pagado': abono.abono_id.valor_pagado * -1,
                        'usuario_uid': abono.abono_id.usuario_uid.id,
                        'tipo_recaudo': abono.abono_id.tipo_recaudo
                    }
                    recaudo = self.env['motgama.recaudo'].create(valores)
                    for valores in valoresPagos:
                        valores.update({'recaudo': recaudo.id})
                        self.env['motgama.pago'].create(valores)
            else:
                revertir = False
        
        if revertir:
            message = 'Se han revertido los abonos seleccionados con abonos negativos correctamente'
        else:
            message = 'No se seleccionó un abono para revertir. No se harán cambios'
        context = dict(self._context or {})
        context['message'] = message
        return {
            'name': 'Proceso completo',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'view_id': self.env.ref('sh_message.sh_message_wizard').id,
            'target': 'new',
            'context': context
        }

class MotgamaLineaRevertirAbonos(models.TransientModel):
    _name = 'motgama.linearevertirabonos'
    _description = 'Linea de Revertir Abonos'

    abono_id = fields.Many2one(string='Abono',comodel_name='motgama.recaudo')
    fecha = fields.Datetime(string='Fecha',readonly=True)
    valor = fields.Float(string='Valor pagado',readonly=True)
    revertir = fields.Boolean(string='Revertir abono',default=False)
    
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
        self.ensure_one()
        if not self.env.user.motgama_ingreso_anticipo:
            raise Warning('No tiene permitido ingresar abonos, contacte al administrador')
        return {
            'name': 'Abonar',
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.abonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    @api.multi
    def revertir_abono(self):
        self.ensure_one()
        return {
            'name': 'Revertir abonos',
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.revertirabonos',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }