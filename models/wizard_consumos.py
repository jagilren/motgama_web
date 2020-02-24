from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardConsumos(models.TransientModel):
    _name = 'motgama.wizard.consumos'
    _desription = 'Wizard de Consumos'

    habitacion_id = fields.Many2one(string='Habitación seleccionada',comodel_name='motgama.flujohabitacion')
    habitacion = fields.Char(string='Habitación')
    hab_permite_consumo = fields.Boolean(string='Habitación Permite Consumo')

    prod_select = fields.Selection(string='Buscar producto',selection=[('cod','Código de barras'),('ref','Referencia de producto'),('nombre','Nombre del producto')])
    prod = fields.Char(string='Producto')
    producto_id = fields.Many2one(string='Producto seleccionado',comodel_name='product.template')
    hay_prod = fields.Boolean(string='Hay producto')

    