from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaDescuento(models.Model):
    _name = 'motgama.descuento'
    _description = 'Descuento'

    movimiento_id = fields.Many2one(string="Movimiento",comodel_name="motgama.movimiento")
    habitacion_id = fields.Many2one(string="Habitación",comodel_name='motgama.flujohabitacion')
    valorDesc = fields.Float(string="Valor descuento")
    linea_id = fields.Many2one(string="Línea de orden de venta",comodel_name="sale.order.line")
    usuario_id = fields.Many2one(string="Usuario",comodel_name="res.users")

    @api.multi
    def aplica_descuento(self):
        self.ensure_one()
        ordenVenta = self.habitacion_id.orden_venta

        paramDesc = self.env['motgama.parametros'].search([('codigo','=','CODDESCSERV')],limit=1)
        if not paramDesc:
            raise Warning('Error: No existe el parámetro "CODDESCSERV"')
        prod_desc = self.env['product.template'].sudo().search([('default_code','=',paramDesc.valor)],limit=1)
        if not prod_desc:
            raise Warning('Error: No existe el producto de código "' + paramDesc.valor + '"')

        valores = {
            'customer_lead' : 0,
            'name' : prod_desc.name,
            'order_id' : ordenVenta.id,
            'price_unit' : 0.0 - self.valorDesc,
            'product_uom_qty' : 1,
            'product_id' : prod_desc.product_variant_id.id,
            'es_hospedaje' : True
        }
        nuevo = self.env['sale.order.line'].sudo().create(valores)
        if not nuevo:
            raise Warning('Error: No se pudo agregar el descuento')

        self.sudo().write({'linea_id': nuevo.id})