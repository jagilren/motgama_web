from odoo import models, fields, api
from datetime import timedelta

class MotgamaSecuenciaDocto(models.Model):
    _name = 'motgama.secuencia.documento'
    _description = 'Secuencia Documento'

    prefijo = fields.Char(string="Prefijo")
    fecha_inicial = fields.Date(string="Fecha inicial (#1)")
    offset = fields.Integer(string="Offset")

    @api.model
    def get_consecutivo(self,fecha=None):
        param = self.env.ref('motgama.secuencia_docto')
        hoy = fecha or fields.Date().today()
        diff = hoy - param.fecha_inicial
        num = diff.days - param.offset
        return param.prefijo + str(num) if param.prefijo else str(num)