from odoo import models, fields, api
from odoo.exceptions import Warning

class WizardReporteHospedaje(models.TransientModel):
    _name = 'motgama.wizard.reportehospedaje'

    fecha_inicial = fields.Datetime(string='Fecha Inicial')
    fecha_final = fields.Datetime(string= 'Fecha final')
    recepcion = fields.Many2one(string='Recepcion',comodel_name='motgama.recepcion')

    @api.multi
    def get_report(self):
        self.ensure_one()

        return{
            'name': 'Reporte de hospedaje',
            'view_mode':'tree',
            'view_id': self.env.ref('motgama.tree_reporte_hospedaje').id,
            'res_model': 'motgama.reportehospedaje',
            'type': 'ir.actions.act_window'
        } 

class ReporteHospedaje(models.TransientModel):
    _name = 'motgama.reportehospedaje'

    recepcion = fields.Many2one(string='Recepcion',comodel_name='motgama.recepcion')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Many2one(string='Habitacion',comodel_name='motgama.flujohabitacion')
    tipoHospedaje = fields.Char(string='Tipo de hospedaje')
    valor = fields.Float(string='Valor')
    usuario = fields.Many2one(string='Usuario',comodel_name='res.users')

    