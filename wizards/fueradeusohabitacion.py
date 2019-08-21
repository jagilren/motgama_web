from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaWizardFueradeuso(models.TransientModel):
    _name = 'motgama.wizardfueradeuso'
    _description = 'Habitación fuera de uso'
    observacion = fields.Char(string='Observaciones')
    usuario_orden = fields.Char(string='Nombre de quien autoriza')

    @api.multi
    def button_fuera_uso(self):
        self.ensure_one()
        habitacion_id = self.env.context['active_id']

        infomovimiento = {
            'habitacion_id':habitacion_id,
            'fueradeusohora':fields.Datetime.now(),
            'fueradeuso_uid':self.env.user.id,
            'fueradeusoobservacion':self.observacion,
            'fueradeuso_usuarioorden':self.usuario_orden
        }
        self.env['motgama.movimiento'].create(infomovimiento)

        # TODO: Enviar correo de movimiento

        self.env['motgama.habitacion'].search([('id','=',habitacion_id)]).write({'estado':'FU'})