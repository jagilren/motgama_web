from odoo import models, fields, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion',ondelete='cascade')
    permite_consumo = fields.Boolean(string='¿Permite Consumo?',default=False)