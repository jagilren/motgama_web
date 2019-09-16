from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaWizardFueradeservicio(models.TransientModel):
    _inherit = 'motgama.wizardfueradeservicio'

    @api.multi
    def button_fuera_servicio(self):
        self.ensure_one()
        habitacion_id = self.env.context['active_id']

        infomovimiento = {      # crea registro de movimiento para fuera de servicio                                P7.0.4R
            'habitacion_id':habitacion_id,
            'fueradeserviciohora':fields.Datetime.now(),
            'fueradeservicio_uid':self.env.user.id,
            'fueradeservicioobservacion':self.observacion
        }
        self.env['motgama.movimiento'].create(infomovimiento)

        # TODO: Enviar correo de movimiento

        self.env['motgama.habitacion'].search([('id','=',habitacion_id)]).write({'estado':'FS'})