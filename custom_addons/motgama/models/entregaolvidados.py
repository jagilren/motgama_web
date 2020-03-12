from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardEntregaolvidados(models.TransientModel):
    _name = 'motgama.wizardentregaolvidados'
    _description = 'Entrega Objetos Olvidados'
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    fecha = fields.Datetime(string=u'fecha entrega',default=lambda self: fields.Datetime().now())
    observacion = fields.Char(string='Observaciones',required=True)
    dardebaja = fields.Boolean(string=u'¿Dar de baja?',default=False)

    @api.multi
    def entregar_objeto(self):
        self.ensure_one()
        if not self.env.user.motgama_entregar_olvidados:
            raise Warning('No tiene permitido entregar objetos olvidados, contacte al administrador')

        if not self.observacion:
            raise Warning('Debe ingresar observaciones')

        idObjeto = self.env.context['active_id']
        objeto = self.env['motgama.objolv'].search([('id','=',idObjeto)],limit=1)

        valores = {
            'entregado': True,
            'entregadofecha': self.fecha,
            'cliente_id': self.cliente_id.id,
            'entregado_uid': self.env.user.id,
            'entregadonota': self.observacion,
            'baja': self.dardebaja,
            'active': False
        }

        objeto.write(valores)