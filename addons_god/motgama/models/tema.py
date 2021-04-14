from odoo import models, fields, api

class MotgamaTema(models.Model):#ok                                                                                 #P7.0.4R
#   Fields: TEMA: .
    _name = 'motgama.tema'
    _description = 'Tema'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string='Código') 
    nombre = fields.Char(string='Nombre',required=True,)
    descripcion = fields.Text(string='Descripción')
    fotografia = fields.Binary(string='Foto')
    active = fields.Boolean(string='Activo?',default=True)
    habitacion_ids = fields.One2many(string='Habitaciones con este tema',comodel_name='motgama.habitacion',inverse_name='tema_id')  #HABITACIONES CON ESTE TEMA