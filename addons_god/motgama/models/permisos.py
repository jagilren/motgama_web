from odoo import models, fields, api

class Permiso(models.Model):
    _name = 'motgama.permiso'
    _description = 'Permisos Motgama'
    _rec_name = 'name'

    tipos = [
        ('flujo','Flujo Habitaciones'),
        ('reserva','Reservas'),
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