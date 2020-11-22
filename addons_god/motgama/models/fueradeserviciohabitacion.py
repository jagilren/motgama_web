from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def fuera_servicio(self):
        if not self.env.ref('motgama.motgama_fuera_servicio') in self.env.user.permisos:
            raise Warning('No tiene permisos para marcar esta habitación como Fuera de Servicio')
        
        return {
            'name': 'Fuera de servicio',
            'type': 'ir.actions.act_window',           
            'res_model': "motgama.wizardfueradeservicio",
            'view_type': "form",
            'view_mode': "form",
            'multi': "True",
            'target': "new"
        }

class MotgamaWizardFueradeservicio(models.TransientModel):
    _inherit = 'motgama.wizardfueradeservicio'

    @api.multi
    def button_fuera_servicio(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_fuera_servicio') in self.env.user.permisos:
            raise Warning('No tiene permitido poner habitaciones en fuera de servicio, contacte al administrador')

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
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.wizardfueradeservicio',
                'tipo_evento': 'correo',
                'asunto': 'La habitación ' + flujo.codigo + ' ha sido puesta Fuera de Servicio',
                'descripcion': 'El usuario ' + self.env.user.name + ' ha puesto la habitación ' + flujo.codigo + ' en estado Fuera de Servicio. Observaciones: ' + str(self.observacion)
            }
            self.env['motgama.log'].create(valores)

        else:
            raise Warning('No se pudo cambiar el estado de la habitación')

        self.refresh_views()
        
        return True