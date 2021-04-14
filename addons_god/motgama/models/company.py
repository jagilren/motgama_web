from odoo import models, fields, api

class Company(models.Model):
    _inherit = 'res.company'

    resol_texto = fields.Text(string='Vista previa')
    footer_factura = fields.Text(string='Pie de página en facturas')