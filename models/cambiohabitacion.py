import pytz
from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaWizardCambiohabitacion(models.TransientModel):
    _inherit = 'motgama.wizardcambiohabitacion'

    @api.multi
    def button_cambio_habitacion(self):
        self.ensure_one()
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        movimiento = flujo.ultmovimiento
        habitacionAnt = self.env['motgama.habitacion'].search([('codigo','=',flujo['codigo'])])
        habitacionAnt_id = habitacionAnt.id

        # busca la nueva habitacion y valida que se encuentre en estado disponible
        habitacion = self.env['motgama.habitacion'].search([('codigo','=',self.nuevaHabitacion)])           
        habitacion_id = habitacion.id
        flujoNuevo = self.env['motgama.flujohabitacion'].search([('codigo','=',habitacion.codigo)])
        if flujoNuevo.estado != 'D':
            raise Warning('La habitación debe estar en estado disponible-'+flujoNuevo.estado)

        if not self.env.user.tz:
            tz = pytz.timezone('America/Bogota')
        else:
            tz = pytz.timezone(self.env.user.tz)
            # Esto me da el numero del dia de la semana, python arranca con 0->lunes
        fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
        nroDia = fechaActualTz.weekday()
        calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
        if not calendario:
            raise Warning('Error: no existe calendario para el dia actual ',int(nroDia))

        # validar que la nueva habitacion si tenga precio
        # validar si se puede cambiar a otra habitacion de menor valor
        # cargar la lista de precio de la nueva habitacion y comparar con el del movimiento,
        # si es mayor o igual hacer el cambio

        # colocar la nueva habitacion en el estado ocupada respectivo ('OO' o 'OA')


        # poner la habitacion anterior en estado aseo 'RC'
