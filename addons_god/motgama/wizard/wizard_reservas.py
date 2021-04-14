from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import Warning
from datetime import datetime, timedelta

class MotgamaWizardModificaReserva(models.TransientModel):
    _name = 'motgama.wizard.modificareserva'
    _description = 'Wizard para modificar reservas'

    cod = fields.Char(string='Código',default=lambda self: self._get_codigo())
    fecha = fields.Datetime(string='Fecha de reserva',default=lambda self: self._get_fecha())
    decoracion = fields.Boolean(string='Con decoración',default=lambda self: self._get_decoracion())
    notadecoracion = fields.Text(string='Nota para la decoración',default=lambda self: self._get_notadecoracion())
    tipohabitacion_id = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo',ondelete='set null',default=lambda self: self._get_tipo())
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='set null',default=lambda self: self._get_habitacion())

    @api.model
    def _get_codigo(self):
        idReserva = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)
        return reserva.cod

    @api.model
    def _get_fecha(self):
        idReserva = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)
        return reserva.fecha
    
    @api.model
    def _get_decoracion(self):
        idReserva = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)
        return reserva.condecoracion
    
    @api.model
    def _get_notadecoracion(self):
        idReserva = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)
        return reserva.notadecoracion
    
    @api.model
    def _get_tipo(self):
        idReserva = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)
        return reserva.tipohabitacion_id

    @api.model
    def _get_habitacion(self):
        idReserva = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)
        return reserva.habitacion_id

    @api.multi
    def button_modificar(self):
        for record in self:
            reserva = self.env['motgama.reserva'].search([('cod','=',record.cod)],limit=1)

            reservas = self.env['motgama.reserva'].search([('habitacion_id','=',record.habitacion_id.id),('cod','!=',record.cod)])
            for reserva in reservas:
                fechaAntes = reserva.fecha - timedelta(days=1)
                fechaDespues = reserva.fecha + timedelta(days=1)
                if fechaAntes < record.fecha < fechaDespues:
                    raise Warning('Esta habitación ya se encuentra reservada para esa fecha')

            valores = {
                'fecha': record.fecha,
                'condecoracion': record.decoracion,
                'notadecoracion': record.notadecoracion,
                'tipohabitacion_id': record.tipohabitacion_id.id,
                'habitacion_id': record.habitacion_id.id,
                'modificada': True,
                'modificada_uid': self.env.user.id,
                'estado': 'modificada'
            }

            if reserva.recaudo_id:
                reserva.recaudo_id.sudo().write({'habitacion':record.habitacion_id.id})

            if record.fecha != reserva.fecha:
                valores.update({'fecha_original': reserva.fecha})

        paramRes = self.env['motgama.parametros'].search([('codigo','=','TIEMPOBLOQRES')],limit=1)
        if not paramRes:
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.reserva',
                'tipo_evento': 'notificacion',
                'asunto': 'Problema con parámetro TIEMPOBLOQRES',
                'descripcion': 'No se ha definido el parámetro TIEMPOBLOQRES, contacte al administrador'
            }
            self.env['motgama.log'].create(valores)
            return reserva.write(valores)
        else:
            try:
                tiempoReserva = int(paramRes.valor)
            except ValueError:
                valores = {
                    'fecha': fields.Datetime().now(),
                    'modelo': 'motgama.reserva',
                    'tipo_evento': 'notificacion',
                    'asunto': 'Problema con parámetro TIEMPOBLOQRES',
                    'descripcion': 'El parámetro TIEMPOBLOQRES está mal definido, contacte al administrador'
                }
                self.env['motgama.log'].create(valores)
                return reserva.write(valores)
            
            if reserva.fecha < fields.Datetime().now() + timedelta(hours=tiempoReserva):
                if reserva.habitacion_id.estado == 'D':
                    reserva.habitacion_id.write({'estado':'R','prox_reserva':record.id,'notificar':True,'sin_alerta':True,'alerta_msg':''})
                else:
                    raise Warning('La habitación no está disponible en este momento')
            
            return reserva.write(valores)

class MotgamaWizardDevolverAnticipo(models.TransientModel):
    _name = 'motgama.wizard.devolveranticipo'
    _description = 'Wizard devolución de anticipo'

    reserva_id = fields.Many2one(string='Reserva',comodel_name='motgama.reserva',default=lambda self: self._get_reserva())
    anticipo = fields.Float(string='Anticipo',default=lambda self: self._get_anticipo(),readonly=True)
    mediopago = fields.Many2one(string='Medio de devolución',comodel_name='motgama.mediopago',required=True)

    @api.model
    def _get_reserva(self):
        return self.env.context['active_id']

    @api.model
    def _get_anticipo(self):
        idRes = self.env.context['active_id']
        reserva = self.env['motgama.reserva'].browse(idRes)
        return reserva.anticipo
    
    @api.multi
    def devolver_anticipo(self):
        self.ensure_one()
        valoresPayment = {
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': self.reserva_id.cliente_id.id,
            'amount': self.anticipo,
            'journal_id': self.mediopago.diario_id.id,
            'payment_date': fields.Date().today(),
            'payment_method_id': 1,
            'communication': 'Revertir anticipo de reserva: ' + self.reserva_id.cod
        }
        paramAnticipos = self.env['motgama.parametros'].search([('codigo','=','CTAANTICIPO')],limit=1)
        if paramAnticipos:
            ant = self.reserva_id.cliente_id.property_account_receivable_id
            cuenta = self.env['account.account'].sudo().search([('code','=',paramAnticipos.valor)],limit=1)
            if not cuenta:
                raise Warning('Se ha definido el parámetro: "CTAANTICIPO" como ' + paramAnticipos.valor + ', pero no existe una cuenta con ese código')
            self.reserva.cliente_id.write({'property_account_receivable_id': cuenta.id})
        payment = self.env['account.payment'].sudo().create(valoresPayment)
        payment.sudo().post()
        if paramAnticipos:
            self.reserva_id.cliente_id.write({'property_account_receivable_id':ant.id})
        
        valoresRecaudo = {
            'cliente': self.reserva_id.cliente_id.id,
            'habitacion': self.reserva_id.habitacion_id.id,
            'total_pagado': -1 * self.anticipo,
            'valor_pagado': -1 * self.anticipo,
            'usuario_uid': self.env.user.id,
            'tipo_recaudo': 'anticipos',
            'recepcion_id': self.env.user.recepcion_id.id
        }
        recaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        valoresPago = {
            'cliente_id': payment.partner_id.id,
            'fecha': fields.Datetime().now(),
            'mediopago': self.mediopago.id,
            'valor': -1 * self.anticipo,
            'usuario_uid': self.env.user.id,
            'pago_id': payment.sudo().id,
            'recaudo': recaudo.id
        }
        pago = self.env['motgama.pago'].create(valoresPago)
        self.reserva_id.write({'anticipo':0.0,'recaudo_id':False})

        return True

class MotgamaWizardRecaudoReserva(models.TransientModel):
    _name = 'motgama.wizard.recaudoreserva'
    _description = 'Recaudo de reserva'

    reserva = fields.Many2one(string='Reserva',comodel_name='motgama.reserva',default=lambda self: self._get_reserva())
    deuda = fields.Float(string='Saldo restante',compute='_compute_deuda')
    total = fields.Float(string='Saldo total',default=lambda self: self._get_total())

    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner',domain="[('customer','=',True)]",default=lambda self: self._get_cliente())
    pagos = fields.Many2many(string='Recaudo',comodel_name='motgama.wizardpago')

    @api.model
    def _get_reserva(self):
        return self.env.context['active_id']

    @api.model
    def _get_total(self):
        reserva = self.env.context['active_id']
        return self.env['motgama.reserva'].search([('id','=',reserva)],limit=1).anticipo
    
    @api.model
    def _get_cliente(self):
        reserva = self.env.context['active_id']
        return self.env['motgama.reserva'].search([('id','=',reserva)],limit=1).cliente_id.id

    @api.depends('pagos.valor')
    def _compute_deuda(self):
        for recaudo in self:
            deuda = recaudo.total
            for pago in recaudo.pagos:
                deuda -= pago.valor
            recaudo.deuda = deuda

    @api.multi
    def recaudar_reserva(self):
        self.ensure_one()
        if abs(self.deuda) >= 0.01:
            raise Warning('La cuenta no ha sido saldada')
        elif self.deuda < 0:
            raise Warning('El valor pagado es mayor al valor de la cuenta')

        valoresPagos = []
        for pago in self.pagos:
            if pago.valor <= 0:
                raise Warning('El valor del pago no puede ser menor o igual a cero')
            valoresPayment = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': self.cliente.id,
                'amount': pago.valor,
                'journal_id': pago.mediopago.diario_id.id,
                'payment_date': fields.Date().today(),
                'payment_method_id': 1,
                'communication': 'Anticipo de ' + self.reserva.cod
            }
            paramAnticipos = self.env['motgama.parametros'].search([('codigo','=','CTAANTICIPO')],limit=1)
            if paramAnticipos:
                ant = self.cliente.property_account_receivable_id
                cuenta = self.env['account.account'].sudo().search([('code','=',paramAnticipos.valor)],limit=1)
                if not cuenta:
                    raise Warning('Se ha definido el parámetro: "CTAANTICIPO" como ' + paramAnticipos.valor + ', pero no existe una cuenta con ese código')
                self.cliente.write({'property_account_receivable_id': cuenta.id})
            payment = self.env['account.payment'].sudo().create(valoresPayment)
            if not payment:
                raise Warning('No se pudo registrar el pago')
            payment.sudo().post()
            if paramAnticipos:
                self.cliente.write({'property_account_receivable_id':ant.id})
            
            valores = {
                'cliente_id': payment.partner_id.id,
                'fecha': fields.Datetime().now(),
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'usuario_uid': self.env.user.id,
                'pago_id': payment.sudo().id
            }
            valoresPagos.append(valores)
        
        valoresRecaudo = {
            'cliente': self.cliente.id,
            'habitacion': self.reserva.habitacion_id.id,
            'total_pagado': self.total,
            'valor_pagado': self.total,
            'usuario_uid': self.env.user.id,
            'tipo_recaudo': 'anticipos',
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
        
        self.reserva.write({'recaudo_id':recaudo.id})
        
        return True

class MotgamaWizardCancelaReserva(models.TransientModel):
    _name = 'motgama.wizard.cancelareserva'
    _description = 'Wizard Cancela Reserva'

    reserva_id = fields.Many2one(string='Reserva',comodel_name='motgama.reserva', default=lambda self: self._get_reserva())

    @api.model
    def _get_reserva(self):
        return self.env.context['active_id']

    @api.multi
    def cancela_reserva(self):
        self.ensure_one()

        if self.reserva_id.habitacion_id.estado == 'R':
            self.reserva_id.habitacion_id.write({'estado':'RC','prox_reserva':False,'sin_alerta':True,'alerta_msg':''})

        valores = {
            'cancelada': True,
            'cancelada_uid':self.env.user.id,
            'fecha_cancela':fields.Datetime().now(),
            'active':False,
            'estado': 'cancelada'
        }
        self.reserva_id.write(valores)