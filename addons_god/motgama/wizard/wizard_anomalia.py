from odoo import models, fields, api
from odoo.exceptions import Warning

class WizardAnomalia(models.TransientModel):
    _name = 'motgama.wizard.anomalia'
    _description = 'Wizard Factura Anomalía'

    factura_id = fields.Many2one(string="Factura",comodel_name="account.invoice",default=lambda self: self._get_factura())
    motivo_anomalia = fields.Char(string="Motivo de la anomalía")

    @api.model
    def _get_factura(self):
        return self.env.context['active_id']

    @api.multi
    def registro_anomalia(self):
        self.ensure_one()
        self.factura_id.sudo().write({
            'factura_anomalia': True,
            'motivo_anomalia': self.motivo_anomalia,
            'fecha_anomalia': fields.Datetime().now()
        })