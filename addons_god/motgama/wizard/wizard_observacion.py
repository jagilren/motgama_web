from odoo import models, fields, api

class MotgamaWizardObservacion(models.TransientModel):
    _name = 'motgama.wizard.observacion'
    _description = 'Wizard Observación'

    habitacion_id = fields.Many2one(string="Habitación",comodel_name="motgama.flujohabitacion",default=lambda self: self._get_habitacion())
    borrar = fields.Boolean(string="Eliminar observación",default=False)
    observacion = fields.Text(string="Observaciones")

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.multi
    def editar_observacion(self):
        self.ensure_one()

        observacion = self.observacion
        if self.borrar:
            observacion = ''
        
        self.habitacion_id.sudo().write({'observacion': observacion})