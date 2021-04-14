from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import Warning
from datetime import datetime, timedelta


class MotgamaReservas(models.Model):#ok
#    Fields: Reserva: se hereda res.partner para ingresar el usuario cuando realiza la reservacion
    _name = 'motgama.reserva'
    _description = 'Reservas'
    _rec_name = 'cod'
    cod = fields.Char(string='Código')
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente',domain=[('customer','=',True),'|',('vat','!=','1'),('vat','=',False)],required=True)
    fecha = fields.Datetime(string='Fecha de reserva',required=True)
    condecoracion = fields.Boolean(string='¿Con decoración?')
    notadecoracion = fields.Text(string='Nota para la decoración')
    tipohabitacion_id = fields.Many2one(string='Tipo de Habitación',comodel_name='motgama.tipo',ondelete='restrict',required=True)
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='restrict',required=True)
    anticipo = fields.Float(string='Anticipo')
    recaudo_id = fields.Many2one(string="Recaudo",comodel_name="motgama.recaudo",ondelete="restrict")
    pago_ids = fields.Many2many(string="Pagos",comodel_name="account.payment")
    modificada = fields.Boolean(string='Reserva Modificada',default=False)
    modificada_uid = fields.Many2one(comodel_name='res.users',string='Usuario que modifica')
    fecha_original = fields.Datetime(string='Fecha de reserva anterior')
    cancelada = fields.Boolean(string='Reserva Cancelada',default=False)
    cancelada_uid = fields.Many2one(comodel_name='res.users',string='Usuario que cancela')
    fecha_cancela = fields.Datetime(string='Fecha de cancelación')
    active = fields.Boolean(string='Activo?',default=True)
    esNueva = fields.Boolean(default=True)
    estado = fields.Selection(string='Estado',selection=[('nueva','Nueva'),('modificada','Modificada'),('reservada','Reservada'),('cancelada','Cancelada'),('finalizada','Finalizada')],default='nueva')

    @api.model
    def create(self,values):
        if self.env.ref('motgama.motgama_crea_reserva') not in self.env.user.permisos:
            raise Warning('No tiene permitido crear reservas')

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
            return record
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
                return record

        if record.fecha < fields.Datetime().now() + timedelta(hours=tiempoReserva):
            if record.habitacion_id.estado == 'D':
                record.habitacion_id.write({'estado':'R','prox_reserva':record.id,'notificar':True,'sin_alerta':True,'alerta_msg':''})
            else:
                raise Warning('La habitación a reservar no está disponible en este momento')

        return record
    
    @api.multi
    def button_modificar(self):
        if self.env.ref('motgama.motgama_edita_reserva') not in self.env.user.permisos:
            raise Warning('No tiene permitido modificar reservas')

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
        if self.env.ref('motgama.motgama_cancela_reserva') not in self.env.user.permisos and self.env.user.id != SUPERUSER_ID:
            raise Warning('No tiene permitido cancelar reservas')

        return {
            'name': 'Cancelar reserva',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.cancelareserva',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.view_wizard_cancela_reserva').id,
            'target': 'new'
        }

    @api.model
    def reservar_cancelar_habitaciones(self):
        reservas = self.env['motgama.reserva'].search([('active','=',True)])
        if not reservas:
            return True

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
            return True
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
            return True

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
            return True
        try:
            tiempoCancelaReserva = int(tiempoCancelaReservaStr.valor)
        except ValueError:
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.reserva',
                'tipo_evento': 'registro',
                'asunto': 'El parámetro "TIEMPOCANCELRES" está mal definido',
                'descripcion': 'No se pudo verificar el estado de las reservas porque el parámetro "TIEMPOCANCELRES" está mal definido'
            }
            self.env['motgama.log'].create(valores)
            return True

        for reserva in reservas:
            intervaloReservar = reserva.fecha - fields.Datetime().now()
            if fields.Datetime().now() < reserva.fecha and intervaloReservar <= timedelta(hours=tiempoReserva):
                if reserva.habitacion_id.estado == 'D':
                    reserva.habitacion_id.write({'estado':'R','prox_reserva':reserva.id,'notificar':True,'sin_alerta':True,'alerta_msg':''})
                else:
                    usuarios = self.env['res.users'].sudo().search([('recepcion_id','=',reserva.habitacion_id.recepcion.id)])
                    uids = [usuario.id for usuario in usuarios]
                    valores = {
                        'fecha': fields.Datetime().now(),
                        'modelo': 'motgama.reserva',
                        'tipo_evento': 'notificacion',
                        'asunto': 'Habitación ' + reserva.habitacion_id.codigo + ' está ocupada y tiene una reserva próxima',
                        'descripcion': 'La habitación ' + reserva.habitacion_id.codigo + ' está reservada para ' + str(reserva.fecha) + ' y en este momento se encuentra ocupada y no pudo ser puesta como Reservada',
                        'notificacion_uids': [(6,0,uids)]
                    }
                    self.env['motgama.log'].create(valores)
            fechaCancelar = reserva.fecha + timedelta(minutes=tiempoCancelaReserva)
            if fields.Datetime().now() >= fechaCancelar:
                if reserva.habitacion_id.estado == 'R':
                    reserva.habitacion_id.write({'estado':'D','prox_reserva':False,'notificar':False,'sin_alerta':True,'alerta_msg':''})
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
    
    @api.multi
    def button_devolver_anticipo(self):
        return {
            'name': 'Devolver anticipo',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.devolveranticipo',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_devolver_anticipo').id,
            'target': 'new'
        }
    
    @api.multi
    def reservar_habitacion(self):
        self.ensure_one()
        tiempoReservaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOBLOQRES')],limit=1)
        if not tiempoReservaStr:
            raise Warning('No se ha definido el parámetro "TIEMPOBLOQRES"')
        try:
            tiempoReserva = int(tiempoReservaStr.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPOBLOQRES" está mal definido')
        tiempoCancelaReservaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOCANCELRES')],limit=1)
        if not tiempoCancelaReservaStr:
            raise Warning('No se ha definido el parámetro "TIEMPOCANCELRES"')
        try:
            tiempoCancelaReserva = int(tiempoReservaStr.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPOCANCELRES" está mal definido')
        
        fecha_inicial = self.fecha - timedelta(hours=tiempoReserva)
        fecha_final = self.fecha + timedelta(minutes=tiempoCancelaReserva)
        if fecha_inicial <= fields.Datetime().now() <= fecha_final:
            if self.habitacion_id.estado == 'D':
                self.habitacion_id.write({'estado':'R','prox_reserva':self.id,'notificar':True,'sin_alerta':True,'alerta_msg':''})
            else:
                raise Warning('La habitación no se encuentra disponible y no puede cambiarse a Reservada')
        else:
            if fields.Datetime().now() < fecha_inicial:
                raise Warning('La habitación solo se puede reservar desde ' + str(tiempoReserva) + ' horas antes de la reserva')
            if fields.Datetime().now() > fecha_final:
                raise Warning('La habitación solo se puede reservar hasta ' + str(tiempoCancelaReserva) + ' minutos después de la reserva, debe modificarla primero')