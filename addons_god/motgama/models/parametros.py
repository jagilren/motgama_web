from odoo import models, fields, api

class MotgamaParametros(models.Model):#ok
#   Fields: PARAMETROS: se deben de definir todos los parametros que se necesitan por sucursal.
    _name = 'motgama.parametros'
    _description = u'parametros'
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    codigo = fields.Char(string=u'Codigo',)
    nombre = fields.Char(string=u'Nombre',)
    valor = fields.Char(string=u'Valor',)
    active = fields.Boolean(string=u'Activo?',default=True)