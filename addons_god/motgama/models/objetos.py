from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaObjetosOlvidados(models.Model):
#    Fields:Objetos Olvidados: elementos que el cliente olvido en una habitacion.
    _name = 'motgama.objolv' #Objetos Olvidados
    _description = 'MotgamaObjetosOlvidados'
    habitacion_id = fields.Many2one(string='Habitacion',comodel_name='motgama.habitacion',ondelete='set null')
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())
    descripcion = fields.Text(string='Descripción')
    valor = fields.Float(string='Valor Estimado')
    encontradopor = fields.Text(string='Encontrado por')
    entregado = fields.Boolean(string='Entregado')
    entregadofecha = fields.Datetime(string='Fecha de entrega') 
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    entregado_uid = fields.Many2one(comodel_name='res.users',string='Usuario que entrega',default=lambda self: self.env.user.id)
    entregadonota = fields.Text(string='Nota')
    baja = fields.Boolean(string='Artículo dado de baja?')
    active = fields.Boolean(string='Activo?', default=True)
    esNuevo = fields.Boolean(default=True)

    @api.model
    def create(self, values):
        record = super().create(values)
        record.esNuevo = False
        return record

class MotgamaObjetosPrestados(models.Model):
#    Fields:Objetos Prestados: elementos que el cliente solicita prestados en su estadia en una habitacion.
    _name = 'motgama.objprestados' #Objetos Prestados
    _description = 'MotgamaObjetosPrestados'
    habitacion_id = fields.Many2one(string='Habitacion',comodel_name='motgama.flujohabitacion',ondelete='set null',required=True)
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',ondelete='restrict')
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())
    objeto = fields.Selection(string='Objeto',selection=[('hielera','Hielera (Con pinza)'),('cobija','Cobija'),('toalla','Toalla'),('utensilios','Utensilios de cocina (Vaso, cuchara, tenedor, cuchillo)'),('almohada','Almohada'),('otro','Otro')])
    descripcion = fields.Text(string='Descripción del objeto')
    prestadopor_uid = fields.Many2one(comodel_name='res.users',string='Usuario que presta',default=lambda self: self.env.user.id)
    estado_devolucion = fields.Selection(string='Estado devolución',selection=[('ok','Devuelto en buen estado'),('mal','Devuelto en mal estado'),('no','No devuelto')])
    devueltofecha = fields.Datetime(string='Fecha de devolución') 
    devuelto_uid = fields.Many2one(comodel_name='res.users',string='Usuario que entrega',default=lambda self: self.env.user.id)
    entregadonota = fields.Text(string='Observaciones')
    active = fields.Boolean(string='Activo?', default=True)
    esNuevo = fields.Boolean(default=True)

    @api.model
    def create(self, values):
        if self.env.ref('motgama.motgama_crea_prestados') not in self.env.user.permisos:
            raise Warning('No está autorizado para prestar objetos')
        record = super().create(values)
        record.esNuevo = False
        return record
    
    @api.onchange('habitacion_id')
    def _onchange_habitacion(self):
        if self.habitacion_id:
            self.movimiento_id = self.habitacion_id.ultmovimiento