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

        codAmanecida = self.env['motgama.parametros'].search([('codigo','=','CODHOSAMANE')])
        if not codAmanecida:
            raise Warning('No existe el parámetro "CODHOSAMANE"')
        prodAmanecida = self.env['product.product'].search([('default_code','=',codAmanecida.valor)])
        if not prodAmanecida:
            raise Warning('No existe producto con Referencia interna: ' + codAmanecida.valor + ' para Hospedaje Amanecida')

        codOcasional = self.env['motgama.parametros'].search([('codigo','=','CODHOSOCASIO')])
        if not codOcasional:
            raise Warning('No existe el parámetro "CODHOSOCASIO"')
        prodOcasional = self.env['product.product'].sudo().search([('default_code','=',codOcasional.valor)])
        if not prodOcasional:
            raise Warning('No existe producto con Referencia interna: ' + codOcasional.valor + ' para Hospedaje Ocasional')

        valores = {
            'customer_lead' : 0,
            'name' : prod_desc.name,
            'order_id' : ordenVenta.id,
            'price_unit' : 0.0 - self.valorDesc,
            'product_uom_qty' : 1,
            'product_id' : prod_desc.product_variant_id.id,
            'es_hospedaje' : True
        }
        if self.habitacion_id.estado == 'LQ':
            base_line = ordenVenta.order_line.filtered(lambda r: r.product_id.id in [prodAmanecida.id,prodOcasional.id])
            if base_line:
                valores['base_line'] = base_line.id
        nuevo = self.env['sale.order.line'].sudo().create(valores)
        if not nuevo:
            raise Warning('Error: No se pudo agregar el descuento')

        self.sudo().write({'linea_id': nuevo.id})