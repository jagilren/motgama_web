from odoo import models, fields, api

class MotgamaWizardEntregaprestados(models.TransientModel):
    _name = 'motgama.wizard_entregaprestados'
    _description = 'Entrega Objetos Prestados'
    fecha = fields.Datetime(string=u'fecha entrega',default=lambda self: fields.Datetime().now())
    observacion = fields.Char(string='Observaciones',required=True)
    devueltook = fields.Boolean(string=u'¿Devuelto ok?',default=False)
    devueltomal = fields.Boolean(string=u'¿Devuelto dañado?',default=False)
    nodevuelto = fields.Boolean(string=u'¿No Devuelto?',default=False)
    estado_devolucion = fields.Selection(string='Estado devolución',selection=[('ok','Devuelto en buen estado'),('mal','Devuelto en mal estado'),('no','No devuelto')],default='ok')

    @api.multi
    def entregar_objetoprestado(self):
        self.ensure_one()

        if not self.observacion:
            raise Warning('Debe ingresar observaciones')

        idObjeto = self.env.context['active_id']
        objeto = self.env['motgama.objprestados'].search([('id','=',idObjeto)],limit=1)

        valores = {
            'devueltook': self.devueltook,
            'devueltomal': self.devueltomal,
            'nodevuelto': self.nodevuelto,
            'devueltofecha': self.fecha,
            'devuelto_uid': self.env.user.id,
            'entregadonota': self.observacion,
            'active': False
        }

        objeto.write(valores)