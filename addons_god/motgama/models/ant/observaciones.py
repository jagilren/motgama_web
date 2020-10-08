from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def edita_observacion(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.observacion',
            'name': 'Editar observación',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

class MotgamaWizardObservacion(models.TransientModel):
    _name = 'motgama.wizard.observacion'
    _description = 'Agregar / Editar observaciones'

    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    observacion = fields.Text(string='Observaciones',default=lambda self: self._get_observacion())
    borrar = fields.Boolean(string='Eliminar observación',default=False)

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.model
    def _get_observacion(self):
        idHab = self.env.context['active_id']
        hab = self.env['motgama.flujohabitacion'].browse(idHab)
        return hab.observacion

    @api.multi
    def editar_observacion(self):
        self.ensure_one()
        ob = self.observacion if not self.borrar else ''
        self.habitacion_id.write({'observacion': ob})