from odoo import models, fields, api

class MotgamaInmotica(models.Model):#ok
    #Fields:Inmotica: Conexion interna entre base de datos.    
    _name = 'motgama.inmotica'
    _description = 'Inmotica'

    habitacion = fields.Char(string='Habitación',required=True)
    parametro = fields.Char(string='Parámetro',required=True)
    evento = fields.Char(string="Evento",required=True)
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())
    usuario_id = fields.Many2one(string='Usuario',comodel_name='res.users',default=lambda self: self.env.user.id)
    mensaje = fields.Selection(string='Tipo de mensaje',selection=[('entrada','Entrada'),('salida','Salida'),('evento','Evento')])

    @api.model
    def create(self,values):
        if values['mensaje'] == 'entrada':
            cod = 'STRINMENT'
        elif values['mensaje'] == 'salida':
            cod = 'STRINMSAL'
        elif values['mensaje'] == 'evento':
            cod = 'STRINMEVEN'
        else:
            raise Warning('Error, los parámetros "STRINMENT", "STRINMSAL" y "STRINMEVEN" están mal definidos, contacte al administrador')
        param = self.env['motgama.parametros'].search([('codigo','=',cod)],limit=1)
        if not param:
            raise Warning('No existe el parámetro con código: "' + cod + '", contacte al administrador')
        values['parametro'] = param.valor
        return super().create(values)