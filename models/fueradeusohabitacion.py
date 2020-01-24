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

class MotgamaZona(models.Model):
    _inherit = 'motgama.zona'

    @api.multi
    def fuera_uso(self):
        self.ensure_one()

        for habitacion_id in self.habitacion_ids:
            flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',habitacion_id.codigo)],limit=1)
            if not flujo or flujo.estado != 'D':
                continue

            reservas = self.env['motgama.reserva'].search([('habitacion_id','=',flujo.id)])
            if reservas:
                continue

            infomovimiento = {      # Crea registro de movimiento para colocar la hab fuera de uso                      P7.0.4R
                'habitacion_id':habitacion_id.id,
                'fueradeusohora':fields.Datetime().now(),
                'fueradeuso_uid':self.env.user.id,
                'observacion':'Zona fuera de uso',
                'fueradeuso_usuarioorden':self.env.user.id
            }
            nuevoMovimiento = self.env['motgama.movimiento'].create(infomovimiento)

            if nuevoMovimiento:
                flujo.sudo().write({'estado':'FU','ultmovimiento':nuevoMovimiento.id,'active':False})
                # TODO: Enviar correo de movimiento
            else:
                raise Warning('No se pudo cambiar el estado de la habitación')

        self.write({'estado':'FU'})
    
    @api.multi
    def habilitar(self):
        self.ensure_one()

        cods = []
        for habitacion_id in self.habitacion_ids:
            flujo = self.env['motgama.flujohabitacion'].search([('codigo','=',habitacion_id.codigo),('active','=',False)],limit=1)
            if not flujo or flujo.estado != 'FU':
                continue

            valoresMovto = {
                'habilitafecha':fields.Datetime().now(),
                'habilita_uid':self.env.user.id,
                'active':False
            }
            flujo.ultmovimiento.write(valoresMovto)

            valoresFlujo = {
                'estado':'D',
                'active':True
            }
            flujo.write(valoresFlujo)
        
        self.write({'estado':'H'})