from odoo import models, fields, api
import json

class MotgamaParametros(models.Model):#ok
#   Fields: PARAMETROS: se deben de definir todos los parametros que se necesitan por sucursal.
    _name = 'motgama.parametros'
    _description = u'parametros'
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null')
    codigo = fields.Char(string=u'Codigo')
    nombre = fields.Char(string=u'Nombre')
    valor = fields.Char(string=u'Valor')
    active = fields.Boolean(string=u'Activo?',default=True)
    valor_text = fields.Text(string="Valor en formato JSON",help="Use este campo si el parámetro se definirá en formato JSON",placeholder='''
        {
            "BEBIDAS": "DCTO_BEBIDAS",
            "RESTAURANTE": "DCTO_RESTAURANTE"
        }
    ''')

    def get_dict(self):
        self.ensure_one()
        if self.valor_text:
            try:
                return json.loads(self.valor_text)
            except Exception:
                pass
        return False