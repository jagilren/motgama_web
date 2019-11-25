from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaWizardFueradeservicio(models.TransientModel):
    _inherit = 'motgama.wizardfueradeservicio'

    @api.multi
    def button_fuera_servicio(self):
        self.ensure_one()
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        habitacion = self.env['motgama.habitacion'].search([('codigo','=',flujo['codigo'])])
        habitacion_id = habitacion.id

        infomovimiento = {      # crea registro de movimiento para fuera de servicio                    #P7.0.4R                       P7.0.4R
            'habitacion_id':habitacion_id,
            'fueradeserviciohora':fields.Datetime.now(),
            'fueradeservicio_uid':self.env.user.id,
            'observacion':self.observacion
        }
        nuevoMovimiento = self.env['motgama.movimiento'].create(infomovimiento)

        if nuevoMovimiento:
            flujo.sudo().write({'estado':'FS','ultmovimiento':nuevoMovimiento.id})
            # TODO: Enviar correo de movimiento

        else:
            raise Warning('No se pudo cambiar el estado de la habitación')

        self.refresh_views()
        
        return True