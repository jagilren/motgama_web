from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaWizardFueradeuso(models.TransientModel):
    _inherit = 'motgama.wizardfueradeuso'

    @api.multi
    def button_fuera_uso(self):
        self.ensure_one()
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        habitacion = self.env['motgama.habitacion'].search([('codigo','=',flujo['codigo'])])
        habitacion_id = habitacion.id

        infomovimiento = {      # Crea registro de movimiento para colocar la hab fuera de uso                      P7.0.4R
            'habitacion_id':habitacion_id,
            'fueradeusohora':fields.Datetime.now(),
            'fueradeuso_uid':self.env.user.id,
            'observacion':self.observacion,
            'fueradeuso_usuarioorden':self.usuario_orden
        }
        nuevoMovimiento = self.env['motgama.movimiento'].create(infomovimiento)

        if nuevoMovimiento:
            flujo.sudo().write({'estado':'FU','ultmovimiento':nuevoMovimiento.id})
            # TODO: Enviar correo de movimiento

        else:
            raise Warning('No se pudo cambiar el estado de la habitación')

        self.refresh_views()

        return True