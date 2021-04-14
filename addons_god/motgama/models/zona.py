from odoo import models, fields, api

class MotgamaZona(models.Model):#ok
#    Fields: ZONA: Zona equivale a pisos que tiene los moteles.                                                     #P7.0.4R
    _name = 'motgama.zona'
    _description = u'Zona'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    _rec_name = 'nombre'
    _order = 'nombre ASC'

    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    recepcion_id = fields.Many2one(string=u'Recepción',comodel_name='motgama.recepcion',ondelete='set null')
    codigo = fields.Char(string=u'Código') 
    nombre = fields.Char(string=u'Nombre de la zona',required=True,)
    active = fields.Boolean(string=u'Activo?',default=True)
    estado = fields.Selection(string='Estado de la zona',selection=[('H','Habilitada'),('FU','Fuera de uso')],default='H')
    habitacion_ids = fields.One2many(string=u'Habitaciones en esta zona',comodel_name='motgama.habitacion',inverse_name='zona_id',) # HABITACION EN ESTA ZONA