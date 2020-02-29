from odoo import fields, models, api
from odoo.exceptions import Warning
from datetime import datetime, timedelta

class MotgamaReservas(models.Model):
    _inherit = 'motgama.reserva'

    @api.model
    def create(self,values):
        record = super().create(values)
        record.esNueva = False
        record.cod = 'Reserva Nro. ' + str(record.id)

        reservas = self.env['motgama.reserva'].search([('habitacion_id','=',record.habitacion_id.id),('id','!=',record.id)])
        for reserva in reservas:
            fechaAntes = reserva.fecha - timedelta(days=1)
            fechaDespues = reserva.fecha + timedelta(days=1)
            if fechaAntes < record.fecha < fechaDespues:
                raise Warning('Esta habitación ya se encuentra reservada para esa fecha')
        
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

        if record.fecha < fields.Datetime().now() + timedelta(hours=tiempoReserva):
            raise Warning('No se puede reservar en menos de ' + str(tiempoReserva) + ' horas')

        return record
    
    @api.multi
    def button_modificar(self):
        return {
            'name': 'Modificar reserva',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.modificareserva',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.form_view_wizard_reserva').id,
            'target': 'new'
        }

    @api.multi
    def button_cancelar(self):
        for reserva in self:
            valores = {
                'cancelada': True,
                'cancelada_uid':self.env.user.id,
                'fecha_cancela':fields.Datetime().now(),
                'active':False
            }
            reserva.write(valores)

    @api.model
    def reservar_cancelar_habitaciones(self):
        reservas = self.env['motgama.reserva'].search([('active','=',True)])
        if not reservas:
            pass

        tiempoReservaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOBLOQRES')],limit=1)
        if not tiempoReservaStr:
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.reserva',
                'tipo_evento': 'registro',
                'asunto': 'No se ha definido el parámetro "TIEMPOBLOQRES"',
                'descripcion': 'No se pudo verificar el estado de las reservas porque no se ha definido el parámetro "TIEMPOBLOQRES"'
            }
            self.env['motgama.log'].create(valores)
            pass
        try:
            tiempoReserva = int(tiempoReservaStr.valor)
        except ValueError:
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.reserva',
                'tipo_evento': 'registro',
                'asunto': 'El parámetro "TIEMPOBLOQRES" está mal definido',
                'descripcion': 'No se pudo verificar el estado de las reservas porque el parámetro "TIEMPOBLOQRES" está mal definido'
            }
            self.env['motgama.log'].create(valores)
            pass

        tiempoCancelaReservaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOCANCELRES')],limit=1)
        if not tiempoCancelaReservaStr:
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.reserva',
                'tipo_evento': 'registro',
                'asunto': 'No se ha definido el parámetro "TIEMPOCANCELRES"',
                'descripcion': 'No se pudo verificar el estado de las reservas porque no se ha definido el parámetro "TIEMPOCANCELRES"'
            }
            self.env['motgama.log'].create(valores)
            pass
        try:
            tiempoCancelaReserva = int(tiempoReservaStr.valor)
        except ValueError:
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.reserva',
                'tipo_evento': 'registro',
                'asunto': 'El parámetro "TIEMPOCANCELRES" está mal definido',
                'descripcion': 'No se pudo verificar el estado de las reservas porque el parámetro "TIEMPOCANCELRES" está mal definido'
            }
            self.env['motgama.log'].create(valores)
            pass

        for reserva in reservas:
            intervaloReservar = reserva.fecha - fields.Datetime().now()
            if fields.Datetime().now() > reserva.fecha and intervaloReservar <= timedelta(hours=tiempoReserva):
                if reserva.habitacion_id.estado == 'D':
                    reserva.habitacion_id.write({'estado':'R','prox_reserva':reserva.id,'notificar':True})
                else:
                    usuarios = self.env['res.users'].search([('recepcion_id','=',reserva.habitacion_id.recepcion.id)])
                    uids = [usuario.id for usuario in usuarios]
                    valores = {
                        'fecha': fields.Datetime().now(),
                        'modelo': 'motgama.reserva',
                        'tipo_evento': 'notificacion',
                        'asunto': 'Habitación ' + reserva.habitacion_id.codigo + ' está ocupada y tiene una reserva próxima',
                        'descripcion': 'La habitación ' + reserva.habitacion_id.codigo + ' está reservada para ' + reserva.fecha + ' y en este momento se encuentra ocupada y no pudo ser puesta como Reservada',
                        'notificacion_uids': [(6,0,uids)]
                    }
                    self.env['motgama.log'].create(valores)
            fechaCancelar = reserva.fecha + timedelta(minutes=tiempoCancelaReserva)
            if fields.Datetime().now() >= fechaCancelar:
                if reserva.habitacion_id.estado == 'R':
                    reserva.habitacion_id.write({'estado':'D','prox_reserva':False,'notificar':False})
                reserva.button_cancelar()
    @api.multi
    def recaudo_anticipo(self):
        self.ensure_one()
        return {
            'name': 'Recaudar anticipo',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.recaudoreserva',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_recaudo_reserva').id,
            'target': 'new'
        }

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
                'modificada_uid': self.env.user.id
            }

            if reserva.recaudo_id:
                reserva.recaudo_id.sudo().write({'habitacion':record.habitacion_id.id})

            if record.fecha != reserva.fecha:
                valores.update({'fecha_original': reserva.fecha})
            
            reserva.write(valores)
            return True

class MotgamaFlujohabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'
    
    @api.multi
    def button_asigna_reserva(self):
        return {
            'name': 'Asignar reserva',
            'type':'ir.actions.act_window',
            'res_model':"motgama.wizardhabitacion",
            'name':"Flujo Habitacion",
            'src_model':"motgama.flujohabitacion",
            'view_type':"form",
            'view_mode':"form",
            'multi':"True",
            'target':"new"
        }

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
            payment = self.env['account.payment'].create(valoresPayment)
            if not payment:
                raise Warning('No se pudo registrar el pago')
            payment.post()
            
            valores = {
                'cliente_id': payment.partner_id.id,
                'fecha': fields.Datetime().now(),
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'usuario_uid': self.env.user.id,
                'pago_id': payment.id
            }
            valoresPagos.append(valores)
        
        valoresRecaudo = {
            'cliente': self.cliente.id,
            'habitacion': self.reserva.habitacion_id.id,
            'total_pagado': self.total,
            'valor_pagado': self.total,
            'usuario_uid': self.env.user.id,
            'tipo_recaudo': 'anticipos'
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