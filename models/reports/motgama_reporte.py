from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaReporte(models.TransientModel):
    _name = 'motgama.reporte'
    _description = 'Modelo para mostrar reportes'

    consumo_ids = fields.Many2many(string='',comodel_name='motgama.consumo',compute="_compute_consumos",store=True)