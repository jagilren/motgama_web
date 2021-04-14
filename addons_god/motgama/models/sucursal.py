from odoo import models, fields, api

class MotgamaSucursal(models.Model):#ok
#    Fields:SUCURSAL: Cada una de las sedes (Moteles).                                                      #P7.0.4R
    _name = 'motgama.sucursal'
    _description = u'Motgama Sucursal'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]

    codigo = fields.Char(string='Código')
    nombre = fields.Char(string='Nombre Sucursal',required=True)
    telefono = fields.Char(string='Teléfono')
    direccion = fields.Text(string='Dirección')
    ciudad = fields.Char(string='Ciudad')
    email = fields.Char(string='Correo Electronico')
    razonsocial_id = fields.Many2one(string='Razón Social',comodel_name='res.company',ondelete='set null')
    nit = fields.Char(string='Nit')# 11 julio 2019
    active = fields.Boolean(string='Activo?', default=True)
    #RECEPCIONES EN ESTA SUCURSAL
    recepcion_ids = fields.One2many(string=u'Recepciones en esta sucursal',comodel_name='motgama.recepcion', inverse_name='sucursal_id')