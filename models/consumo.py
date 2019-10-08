from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')

class StockLocation(models.Model):
    _inherit = 'stock.location'

    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion',ondelete='cascade')
    permite_consumo = fields.Boolean(string='¿Permite Consumo?',default=False)

class MotgamaConsumo(models.Model):
    _inherit = 'motgama.consumo'

    @api.model
    def create(self,values):
        if values['cantidad'] == 0:
            raise Warning('Debe especificar una cantidad mayor a cero')
        record = super().create(values)

        cliente = self.env['res.partner'].search([('vat','=','1')], limit=1)
        if not cliente:
            raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')

        valoresTransferencia = {
            'location_id' : self.env['stock.location'].search([('id','=',record.lugar_id.id)],limit=1).id,
            'location_dest_id' : self.env.ref('stock.stock_location_stock').id,
            'picking_type_id' : self.env['stock.picking.type'].search([('code','=','internal')],limit=1).id,
            'move_type' : 'direct',
            'company_id' : self.env.user.company_id.id
        }
        transferencia = self.env['stock.picking'].create(valoresTransferencia)
        if not transferencia:
            raise Warning('No se pudo crear la transferencia de inventario')

        valoresLineaTransferencia = {
            'company_id' : transferencia.company_id.id,
            'date' : fields.Datetime.now(),
            'date_expected' : fields.Datetime.now(),
            'location_dest_id' : transferencia.location_dest_id.id,
            'location_id' : transferencia.location_id.id,
            'product_id' : record.producto_id.product_variant_id.id,
            'product_uom' : record.producto_id.uom_id.id,
            'product_uom_qty' : record.cantidad,
            'picking_id' : transferencia.id,
            'name' : record.producto_id.product_variant_id.name + '/' + transferencia.location_id.name + '/' + transferencia.location_dest_id.name
        }
        lineaTransferencia = self.env['stock.move'].create(valoresLineaTransferencia)
        if not lineaTransferencia:
            raise Warning('No se pudo crear la transferencia de inventario')
        transferencia.action_confirm()
        transferencia.action_assign()
        if transferencia.state != 'assigned':
            valoresLineaMovimiento = {
                'date' : fields.Datetime.now(),
                'location_dest_id' : transferencia.location_dest_id.id,
                'location_id' : transferencia.location_id.id,
                'product_id' : record.producto_id.product_variant_id.id,
                'product_uom_id' : record.producto_id.uom_id.id,
                'product_uom_qty' : 0,
                'picking_id' : transferencia.id,
                'move_id' : lineaTransferencia.id,
                'qty_done' : record.cantidad
            }
            lineaMovimiento = self.env['stock.move.line'].create(valoresLineaMovimiento)
            if not lineaMovimiento:
                raise Warning('Error al asentar el movimiento de inventario')
            transferencia.button_validate()
            # TODO: Mostrar mensaje de no hay disponibilidad
        else:
            reservado = lineaTransferencia.reserved_availability
            pedido = record.cantidad
            if reservado < pedido:
                for linea in lineaTransferencia.move_line_ids:
                    linea.write({'qty_done':record.cantidad})
                transferencia.button_validate()
                # TODO: Mostrar mensaje de no hay disponibilidad
            else:
                movimientos = transferencia.move_line_ids
                for movimiento in movimientos:
                    movimiento.write({'qty_done':movimiento.product_uom_qty})
                transferencia.button_validate()

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
            raise Warning('Error al registrar el consumo: No se pudo agregar el consumo a la orden de venta')

        entregas = ordenVenta.picking_ids
        for entrega in entregas:
            if entrega.state == 'assigned':
                movimientos = entrega.move_line_ids
                for movimiento in movimientos:
                    movimiento.write({'qty_done':movimiento.product_uom_qty})
                entrega.button_validate()
        
        return record