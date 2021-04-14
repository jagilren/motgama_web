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
            else:
                raise Warning('No se pudo cambiar el estado de la habitación')

        self.write({'estado':'FU'})
        valores = {
            'fecha': fields.Datetime().now(),
            'modelo': 'motgama.zona',
            'tipo_evento': 'correo',
            'asunto': 'La zona ' + self.nombre + ' ha sido puesta Fuera de Uso',
            'descripcion': 'El usuario ' + self.env.user.name + ' ha puesto la zona ' + self.nombre + ' en estado Fuera de Uso.'
        }
        self.env['motgama.log'].create(valores)
    
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