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
            cliente = self.env.ref('motgama.cliente_contado')
            valoresPayment = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': cliente.id,
                'amount': pago.valor,
                'journal_id': pago.mediopago.diario_id.id,
                'payment_date': fields.Date().today(),
                'payment_method_id': 1,
                'communication': 'Abono para movimiento con id: ' + str(self.movimiento_id.id)
            }
            paramAnticipos = self.env['motgama.parametros'].search([('codigo','=','CTAANTICIPO')],limit=1)
            if paramAnticipos:
                ant = cliente.property_account_receivable_id
                cuenta = self.env['account.account'].sudo().search([('code','=',paramAnticipos.valor)],limit=1)
                if not cuenta:
                    raise Warning('Se ha definido el parámetro: "CTAANTICIPO" como ' + paramAnticipos.valor + ', pero no existe una cuenta con ese código')
                cliente.write({'property_account_receivable_id': cuenta.id})
            payment = self.env['account.payment'].sudo().create(valoresPayment)
            if not payment:
                raise Warning('No se pudo registrar el pago')
            payment.sudo().post()
            if paramAnticipos:
                cliente.write({'property_account_receivable_id':ant.id})
            
            valores = {
                'cliente_id': self.env.ref('motgama.cliente_contado').id,
                'fecha': fields.Datetime().now(),
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'usuario_uid': self.env.user.id,
                'pago_id': payment.sudo().id
            }
            valoresPagos.append(valores)
        
        hab = self.env['motgama.flujohabitacion'].search([('codigo','=',self.movimiento_id.habitacion_id.codigo)],limit=1)
        if not hab:
            raise Warning('Hay un problema con la habitación')

        valoresRecaudo = {
            'movimiento_id': self.movimiento_id.id,
            'cliente': self.env.ref('motgama.cliente_contado').id,
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
    abono_ids = fields.Many2many(string='Abonos a revertir',comodel_name='motgama.recaudo',default=lambda self: self._get_abonos())
    total_abonado = fields.Float(string='Abonado anteriormente',readonly=True, default=lambda self: self._get_abonado())
    total_abonos = fields.Float(string='Total abonos',compute="_compute_abonos")
    mediopago = fields.Many2one(string='Medio de pago',comodel_name='motgama.mediopago',required=True)
    total_revertir = fields.Float(string='Valor a devolver',default=0.0)

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']
    
    @api.model
    def _get_abonos(self):
        habitacion = self.env['motgama.flujohabitacion'].browse(self.env.context['active_id'])
        recaudos = habitacion.ultmovimiento.recaudo_ids
        ids = [recaudo.id for recaudo in recaudos]
        return [(6,0,ids)]
    
    @api.model
    def _get_abonado(self):
        habitacion = self.env['motgama.flujohabitacion'].browse(self.env.context['active_id'])
        abonado = 0.0
        for recaudo in habitacion.ultmovimiento.recaudo_ids:
            abonado += recaudo.valor_pagado
        return abonado
    
    @api.depends('total_revertir','total_abonado')
    def _compute_abonos(self):
        for record in self:
            record.total_abonos = record.total_abonado - record.total_revertir

    @api.multi
    def revertir_abonos(self):
        self.ensure_one()
        if self.total_abonos < 0:
            raise Warning('No puede devolver un valor mayor al total abonado por el cliente')
        if self.total_revertir == 0:
            raise Warning("No puede devolver $0")

        cliente = self.env.ref('motgama.cliente_contado')

        valoresPayment = {
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': cliente.id,
            'amount': self.total_revertir,
            'journal_id': self.mediopago.diario_id.id,
            'payment_date': fields.Date().today(),
            'payment_method_id': 1,
            'communication': 'Revertir abono de movimiento con id: ' + str(self.habitacion_id.ultmovimiento.id)
        }
        paramAnticipos = self.env['motgama.parametros'].search([('codigo','=','CTAANTICIPO')],limit=1)
        if paramAnticipos:
            ant = cliente.property_account_receivable_id
            cuenta = self.env['account.account'].sudo().search([('code','=',paramAnticipos.valor)],limit=1)
            if not cuenta:
                raise Warning('Se ha definido el parámetro: "CTAANTICIPO" como ' + paramAnticipos.valor + ', pero no existe una cuenta con ese código')
            cliente.write({'property_account_receivable_id': cuenta.id})
        payment = self.env['account.payment'].sudo().create(valoresPayment)
        payment.sudo().post()
        if paramAnticipos:
                cliente.write({'property_account_receivable_id':ant.id})

        move_lines_ids = []
        for abono in self.abono_ids:
            for pago in abono.pagos:
                move_name = pago.pago_id.move_name
                move = self.env['account.move'].sudo().search([('name','=',move_name)],limit=1)
                move_lines_ids.extend(move.line_ids.filtered(lambda r: r.account_id.reconcile).ids)
        move = self.env['account.move'].sudo().search([('name','=',payment.sudo().move_name)],limit=1)
        move_lines_ids.extend(move.line_ids.filtered(lambda r: r.account_id.reconcile).ids)
        lines = self.env['account.move.line'].sudo().browse(move_lines_ids)
        lines.sudo().reconcile()

        valoresRecaudo = {
            'movimiento_id': self.habitacion_id.ultmovimiento.id,
            'habitacion': self.habitacion_id.id,
            'cliente': self.env.ref('motgama.cliente_contado').id,
            'total_pagado': self.total_revertir * -1,
            'valor_pagado': self.total_revertir * -1,
            'usuario_uid': self.env.user.id,
            'tipo_recaudo': 'abonos'
        }
        recaudo = self.env['motgama.recaudo'].create(valoresRecaudo)

        valoresPago = {
            'movimiento_id': self.habitacion_id.ultmovimiento.id,
            'mediopago': self.mediopago.id,
            'valor': self.total_revertir * -1,
            'fecha': fields.Datetime().now(),
            'cliente_id': self.env.ref('motgama.cliente_contado').id,
            'usuario_uid': self.env.user.id,
            'pago_id': payment.sudo().id,
            'recaudo': recaudo.id
        }
        pago = self.env['motgama.pago'].create(valoresPago)
        if not pago:
            raise Warning('Error al revertir los abonos')

        message = 'Se ha revertido $ ' + str(self.total_revertir) + ' para un total abonado de: $ ' + str(self.total_abonos)
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