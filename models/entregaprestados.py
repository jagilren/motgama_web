from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardEntregaprestados(models.TransientModel):
    _name = 'motgama.wizard_entregaprestados'
    _description = 'Entrega Objetos Prestados'
    fecha = fields.Datetime(string=u'fecha entrega',default=lambda self: fields.Datetime().now())
    observacion = fields.Char(string='Observaciones')
    estado_devolucion = fields.Selection(string='Estado devolución',selection=[('ok','Devuelto en buen estado'),('mal','Devuelto en mal estado'),('no','No devuelto')],default='ok')

    @api.multi
    def entregar_objeto(self):
        self.ensure_one()
        if not self.env.user.motgama_devuelve_prestados:
            raise Warning('No tiene permitido devolver objetos prestados, contacte al administrador')

        idObjeto = self.env.context['active_id']
        objeto = self.env['motgama.objprestados'].search([('id','=',idObjeto)],limit=1)

        valores = {
            'devueltofecha': self.fecha,
            'devuelto_uid': self.env.user.id,
            'entregadonota': self.observacion,
            'estado_devolucion': self.estado_devolucion,
            'active': False
        }

        objeto.write(valores)
        objeto.habitacion_id.refresh_views()