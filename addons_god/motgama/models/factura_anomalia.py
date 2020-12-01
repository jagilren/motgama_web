from odoo import models, fields, api
from odoo.exceptions import Warning

class Invoice(models.Model):
    _inherit = 'account.invoice'

    factura_anomalia = fields.Boolean(string="Factura con anomalía")
    motivo_anomalia = fields.Char(string="Motivo de la anomalía")
    fecha_anomalia = fields.Datetime(string="Fecha y hora de la anomalía")

    @api.multi
    def registro_anomalia(self):
        if self.env.ref('motgama.motgama_factura_anomalia') not in self.env.user.permisos:
            raise Warning('No tiene permitido registrar anomalías')
        
        return {
            'name': 'Registrar anomalía',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.anomalia',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.view_wizard_anomalia').id,
            'target': 'new'
        }

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