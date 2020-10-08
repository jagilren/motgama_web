from odoo import models, fields, api

class StockAuxReport(models.TransientModel):
    _name = 'stock_aux_report.stock_aux_report'
    _order = 'id asc'

    asociado = fields.Char(string='Asociado')
    producto = fields.Char(string='Producto')
    ubicacion = fields.Char(string='Ubicación')
    inicial = fields.Float(string='Cantidad inicial')
    product_in = fields.Float(string='Cantidad que ingresa')
    product_out = fields.Float(string='Cantidad que sale')
    total = fields.Float(string='Cantidad total')