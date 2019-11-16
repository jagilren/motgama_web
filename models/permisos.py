from odoo import models, fields, api, _

class Users(models.Model):
    _inherit = "res.users"

    motgama_consumo_negativo = fields.Boolean(string='Puede agregar consumos negativos',default=False)

    