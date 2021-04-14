from odoo import models, fields, api

class MotgamaPagos(models.Model):
    _name = 'motgama.pago'
    _description = 'Pago'
    movimiento_id = fields.Integer('Nro. Movimiento')
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente',required=True)   
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())   
    mediopago = fields.Many2one(string='Medio de Pago',comodel_name='motgama.mediopago',required=True)
    valor =  fields.Float(string='Valor a pagar',required=True)
    # Se debe hacer la condicional que si el usuario va a pagar con prenda entonces se debe agregar el contacto que nos aparece desde odoo    
    descripcion = fields.Text(string='Descripcion')
    usuario_uid = fields.Integer(string='responsable',default=lambda self: self.env.user.id)
    recaudo = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo',ondelete='restrict')
    pago_id = fields.Many2one(string='Pago',comodel_name='account.payment')

class MotgamaRecaudo(models.Model):
    _name = 'motgama.recaudo'
    _description = 'Recaudo de hospedaje'
    _rec_name = 'nrorecaudo'

    nrorecaudo = fields.Char(string='Recaudo nro.',required=True,default='Nuevo')
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    recepcion_id = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')
    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    total_pagado = fields.Float(string='Valor total')
    pagos = fields.One2many(string='Pagos',comodel_name='motgama.pago',inverse_name='recaudo')
    prenda = fields.Many2one(string='Prenda asociada',comodel_name='motgama.prendas')
    valor_pagado = fields.Float(string='Valor pagado',default=0.0)
    usuario_uid = fields.Many2one(string='Usuario que recauda',comodel_name='res.users', default=lambda self: self.env.user.id)
    tipo_recaudo = fields.Selection(string='Tipo de recaudo',selection=[('habitaciones','Recaudo de habitaciones'),('abonos','Recaudo de abonos'),('prenda','Recaudo de prenda'),('anticipos','Recaudo de anticipos'),('otros','Otros recaudos')])
    estado = fields.Selection(string='Estado',selection=[('pagado','Pagado'),('anulado','Anulado')],default='pagado')
    modificado = fields.Boolean(string="Modificado",default=False)
    active = fields.Boolean(string='Activo',default=True)

    @api.model
    def create(self,values):
        if values.get('nrorecaudo','Nuevo') == 'Nuevo':
            values['nrorecaudo'] = self.env['ir.sequence'].next_by_code('motgama.recaudo') or 'Nuevo'
        return super().create(values)

class MotgamaMedioPago(models.Model):
    _name = 'motgama.mediopago'
    _description = 'Medios de Pago'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre',required=True)
    tipo = fields.Selection(string='Tipo de pago',required=True,selection=[('electro','Electrónico'),('efectivo','Efectivo'),('pase','Pase/Cortesía'),('prenda','Prenda'),('abono','Abono')])
    lleva_prenda = fields.Boolean(string='¿Lleva Prenda?',compute='_compute_prenda')
    diario_id = fields.Many2one(string='Diario de pago',comodel_name='account.journal')
    active = fields.Boolean(string='Activo',default=True)
    cod = fields.Char(string="Código",size=2)

    @api.onchange('nombre')
    def onchange_nombre(self):
        if self.nombre:
            self.cod = self.nombre[:2].upper()

    @api.depends('tipo')
    def _compute_prenda(self):
        for record in self:
            record.lleva_prenda = record.tipo == 'prenda'