from odoo import models, fields, api, _

class Users(models.Model):
    _inherit = "res.users"

    # Campo de permisos
    permisos = fields.Many2many(string='Permisos Motgama',comodel_name='motgama.permiso')

class Permiso(models.Model):
    _name = 'motgama.permiso'
    _description = 'Permisos Motgama'
    _rec_name = 'name'

    tipos = [
        ('flujo','Flujo Habitaciones'),
        ('consumo','Consumos'),
        ('desc','Descuentos y bonos'),
        ('prenda','Prendas'),
        ('anticipos','Anticipos'),
        ('prestados','Objetos prestados'),
        ('factura','Facturación'),
        ('olvidados','Objetos olvidados'),
        ('informes','Informes'),
        ('admin','Administración')
    ]

    name = fields.Char(string='Nombre', required=True)
    tipo = fields.Selection(string="Tipo de permiso", selection=tipos)