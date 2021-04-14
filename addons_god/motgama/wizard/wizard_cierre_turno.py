from odoo import models, fields, api

class MotgamaCierreTurno(models.TransientModel):
    _name = 'motgama.cierreturno'
    _description = 'Cierre Turno'
    usuarioturno_uid = fields.Integer(string=u'responsable',) # OJO ENLAZAR AL USUARIO LOGUEADO EN EL TURNO
    ultmovimiento_id = fields.Integer('Ultimo Movimiento')
    ultctacobro = fields.Integer('Ultima Cta. Cobro')
    ultfactura = fields.Char('Ultima Factura')
    fecha = fields.Date(string=u'Fecha')
    hora = fields.Datetime(string=u'Hora')