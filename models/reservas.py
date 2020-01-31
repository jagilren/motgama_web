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
            # TODO: Notificar en vez de raise
            pass
        try:
            tiempoReserva = int(paramRes.valor)
        except ValueError:
            # TODO: Notificar en vez de raise
            pass

        if record.fecha < fields.Datetime().now() + timedelta(hours=tiempoReserva):
            raise Warning('No se puede reservar en menos de ' + str(tiempoReserva) + ' horas')

        return record
    
    @api.multi
    def button_modificar(self):
        return {
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
            idReserva = self.env.context['active_id']
            reserva = self.env['motgama.reserva'].search([('id','=',idReserva)],limit=1)

            valores = {
                'fecha': record.fecha,
                'condecoracion': record.decoracion,
                'notadecoracion': record.notadecoracion,
                'tipohabitacion_id': record.tipohabitacion_id,
                'habitacion_id': record.habitacion_id,
                'modificada': True,
                'modificada_uid': self.env.user.id
            }

            if record.fecha != reserva.fecha:
                valores.update({'fecha_original': reserva.fecha})
            
            reserva.write(valores)
            return True

class MotgamaFlujohabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'
    
    @api.multi
    def button_asigna_reserva(self):
        return {
            'type':'ir.actions.act_window',
            'res_model':"motgama.wizardhabitacion",
            'name':"Flujo Habitacion",
            'src_model':"motgama.flujohabitacion",
            'view_type':"form",
            'view_mode':"form",
            'multi':"True",
            'target':"new"
        }
        