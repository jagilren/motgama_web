from odoo import models, fields, api

class Account(models.Model):
    _inherit = 'account.account'

    ccosto = fields.Boolean(string="Lleva Centro de Costo en Interfaz",default=False)
    lleva_nit = fields.Boolean(string="Lleva NIT por defecto")
    nit = fields.Char(string="NIT")