from odoo import models, fields, api

class Account(models.Model):
    _inherit = 'account.account'

    ccosto = fields.Boolean(string="Lleva Centro de Costo en Interfaz",default=False)
    con_nit = fields.Boolean(string="Lleva NIT del asociado en interfaz contable")
    lleva_nit = fields.Boolean(string="Lleva NIT por defecto en interfaz contable")
    nit = fields.Char(string="NIT")