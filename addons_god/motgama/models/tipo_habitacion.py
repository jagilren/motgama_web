from odoo import models, fields, api

class MotgamaTipo(models.Model):#ok Tipo de habitaciones
#    Fields: TIPO DE HABITACION: Caracteristicas de las habitaciones y datos generales para el mismo tipo
    _name = 'motgama.tipo'
    _description = u'Tipo de habitación'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    codigo = fields.Char(string=u'Código') 
    nombre = fields.Char(string=u'Nombre',required=True,)
    tiemponormalocasional = fields.Integer(string=u'Tiempo normal')
    # minibar = fields.Boolean(string=u'Minibar',)
    # turco = fields.Boolean(string=u'Turco',)
    # jacuzzi = fields.Boolean(string=u'Jacuzzi',)
    # camamov = fields.Boolean(string=u'Cama Movil',)
    # smartv = fields.Boolean(string=u'Smart TV',)
    # barrasonido = fields.Boolean(string=u'Barra Sonido',)
    # hometheater = fields.Boolean(string=u'Home Theater')
    # poledance = fields.Boolean(string=u'Pole Dance',)
    # sillatantra = fields.Boolean(string=u'Silla Tantra')
    # columpio = fields.Boolean(string=u'Columpio')
    # aireacond = fields.Boolean(string=u'Aire Acond')
    # garajecarro = fields.Boolean(string=u'Garaje Carro')
    # garajemoto = fields.Boolean(string=u'Garaje Moto')
    # piscina = fields.Boolean(string=u'Piscina')
    # miniteca = fields.Boolean(string=u'Miniteca')
    # sauna = fields.Boolean(string=u'Sauna')
    # balcon = fields.Boolean(string=u'Balcon')
    active = fields.Boolean(string=u'Activo?',default=True)
    # Comodidades del tipo de habitación
    comodidades = fields.Many2many(string='Comodidades',comodel_name='motgama.comodidad')
    # Habitaciones con este tipo 
    habitacion_ids = fields.One2many(string=u'Habitaciones con este tipo',comodel_name='motgama.habitacion',inverse_name='tipo_id')
    # Enlaza las listas de precios por tipo
    listapreciotipo_ids = fields.One2many('motgama.listapreciotipo', 'tipo_id', string='Listas de precios')