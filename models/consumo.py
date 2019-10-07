from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')

class MotgamaConsumo(models.Model):
    _inherit = 'motgama.consumo'

    @api.model
    def create(self,values):
        record = super().create(values)

        cliente = self.env['res.partner'].search([('vat','=','1')], limit=1)
        if not cliente:
            raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')

        ordenVenta = self.env['sale.order'].search(['&',('movimiento','=',record.movimiento_id),('state','=','sale')], limit=1)
        if not ordenVenta:
            valores = {
                'partner_id' : cliente.id,
                'movimiento' : record.movimiento_id
            }
            ordenVenta = self.env['sale.order'].create(valores)
            if not ordenVenta:
                raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
            ordenVenta.action_confirm()

        valoresLinea = {
            'customer_lead' : 0,
            'name' : record.producto_id.name,
            'order_id' : ordenVenta.id,
            'price_unit' : record.vlrUnitario,
            'product_uom_qty' : record.cantidad,
            'product_id' : record.producto_id.product_variant_id.id
        }
        nuevaLinea = self.env['sale.order.line'].create(valoresLinea)
        if not nuevaLinea:
            raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
        
        return record
