from odoo import models, fields, api

class MotgamaReasignacion(models.Model):
    _name = 'motgama.reasignacion'
    _description = 'Reasignaciones de habitaciones'
    # _rec_name = 'codigo'
    habitacion_anterior = fields.Many2one(string='Habitación anterior',comodel_name='motgama.flujohabitacion')
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    fechareasigna = fields.Datetime(string='Fecha de reasignación',default=lambda self: fields.Datetime().now())
    habitacion_nueva = fields.Many2one(string='Habitación nueva',comodel_name='motgama.flujohabitacion')
    descripcion = fields.Char(string='Observaciones')
    active = fields.Boolean(string='Activo?',default=True)
    usuario_id = fields.Many2one(string="Usuario responsable",comodel_name="res.users")