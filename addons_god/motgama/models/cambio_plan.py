from odoo import models, fields, api

class MotgamaCambioPlan(models.Model):
    _name = 'motgama.cambioplan'
    _description = 'Registro de cambio de plan de habitación'

    fecha = fields.Datetime(string='Fecha del cambio',default=lambda self: fields.Datetime().now())
    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    plan_anterior = fields.Selection(string='Plan anterior',selection=[('OO','Ocasional'),('OA','Amanecida')])
    plan_nuevo = fields.Selection(string='Plan nuevo',selection=[('OO','Ocasional'),('OA','Amanecida')])
    usuario_id = fields.Many2one(string="Usuario responsable",comodel_name="res.users")