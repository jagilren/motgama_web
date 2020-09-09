from odoo import models, fields, api, _

class Users(models.Model):
    _inherit = "res.users"

    # Campo de permisos
    permisos = fields.Many2many(string='Permisos Motgama',comodel_name='motgama.permiso')

class Permiso(models.Model):
    _name = 'motgama.permiso'
    _description = 'Permisos Motgama'

    name = fields.Char(string='Nombre', required=True)