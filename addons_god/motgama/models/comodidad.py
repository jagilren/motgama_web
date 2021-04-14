from odoo import models, fields, api

class MotgamaComodidad(models.Model):
    _name = 'motgama.comodidad'
    _description = 'Comodidades de la habitación'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre')