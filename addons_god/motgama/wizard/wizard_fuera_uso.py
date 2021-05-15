from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardFueradeuso(models.TransientModel):
    _name = 'motgama.wizardfueradeuso'
    _description = 'Habitación fuera de uso'
    observacion = fields.Text(string='Observaciones')
    usuario_orden = fields.Char(string='Nombre de quien autoriza')

    @api.multi
    def button_fuera_uso(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_fuera_uso') in self.env.user.permisos:
            raise Warning('No tiene permitido poner habitaciones en fuera de uso, contacte al administrador')

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
            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.wizardfueradeuso',
                'tipo_evento': 'correo',
                'asunto': 'La habitación ' + flujo.codigo + ' ha sido puesta Fuera de Servicio',
                'descripcion': 'El usuario ' + self.env.user.name + ' ha puesto la habitación ' + flujo.codigo + ' en estado Fuera de Uso. Observaciones: ' + str(self.observacion)
            }
            self.env['motgama.log'].create(valores)

        else:
            raise Warning('No se pudo cambiar el estado de la habitación')

        self.refresh_views()

        return True