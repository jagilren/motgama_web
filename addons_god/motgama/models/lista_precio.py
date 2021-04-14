from odoo import models, fields, api

class MotgamaListaPrecioTipo(models.Model): #Lista de precios por tipo de habitacion
    _name = 'motgama.listapreciotipo'
    _description = 'Listas de Precios por tipo de habitación'
    nombrelista = fields.Selection([('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')], string='Lista')
    tipo_id = fields.Many2one('motgama.tipo','Tipo habitación')
    tarifaocasional = fields.Float(string=u'Precio Ocasional')
    tarifamanecida = fields.Float(string=u'Precio Amanecida')
    tarifahoradicional = fields.Float(string=u'Precio hora adicional')
    active = fields.Boolean(string=u'Activo?',default=True)    
    #tipo_id = fields.Many2one(string=u'Tipo',comodel_name='motgama.habitacion',ondelete='set null',)

class MotgamaListaPrecioHabitacion(models.Model): #Lista de precios por habitacion                                          #P7.0.4R
    _name = 'motgama.listapreciohabitacion'
    _description = 'Listas de Precios para esta habitacion'
    nombrelista = fields.Selection([('1', 'L1'),('2', 'L2'),('3', 'L3'),('4', 'L4'),('5', 'L5')], string='Lista')
    tarifaocasional = fields.Float(string=u'Precio Ocasional')
    tarifamanecida = fields.Float(string=u'Precio Amanecida')
    tarifahoradicional = fields.Float(string=u'Precio hora adicional')
    active = fields.Boolean(string=u'Activo?',default=True)
    habitacion_id = fields.Many2one(string=u'Habitacion',comodel_name='motgama.habitacion',ondelete='set null',)