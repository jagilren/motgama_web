from odoo import models, fields, api

class MotgamaComanda(models.Model):
#    Fields: Comandas
    _name = 'motgama.comanda'
    _description = 'Comanda'
    _rec_name = 'nrocomanda'
    _inherit  = 'base'
    # 19 jun se cambia por habitacion para despues realizar un autoguardado
    nrocomanda = fields.Integer(string='Nro. Comanda')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Integer(string='Movimiento')
    producto_id = fields.Many2one(string='Producto',comodel_name='product.template',ondelete='set null',required=True)   
    cantidad = fields.Float(string='Cantidad',required=True)                                                                                   #P7.0.4R
    descripcion = fields.Text(string='Descripción')
    usuario_id = fields.Many2one(string='Usuario',comodel_name='res.users',default=lambda self: self.env.user.id)
    recepcion_id = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')
    active = fields.Boolean(string='Activo?',default=True)

    @api.model
    def create(self,values):
        record = super(MotgamaComanda, self).create(values)
        self.refresh_views()
        return record