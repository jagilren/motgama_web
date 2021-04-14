from odoo import models, fields, api

class Users(models.Model):
    _inherit = "res.users"

    recepcion_id = fields.Many2one(string=u'Recepción',comodel_name='motgama.recepcion',ondelete='set null')
    # Campo de permisos
    permisos = fields.Many2many(string='Permisos Motgama',comodel_name='motgama.permiso')