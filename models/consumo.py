from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')

class StockLocation(models.Model):
    _inherit = 'stock.location'

    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion',ondelete='cascade')
    permite_consumo = fields.Boolean(string='¿Permite Consumo?',default=False)

class ProductCategory(models.Model):
    _inherit = 'product.category'

    llevaComanda = fields.Boolean(string='¿Lleva Comanda?',default=False)

class MotgamaConsumo(models.Model):
    _inherit = 'motgama.consumo'

    @api.model
    def create(self,values):
        cliente = self.env['res.partner'].search([('vat','=','1')], limit=1)
        if not cliente:
            raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')

        if values['cantidad'] == 0:
            raise Warning('Debe especificar una cantidad mayor a cero')
        elif values['cantidad'] < 0:
            if not self.env.user.motgama_consumo_negativo:
               raise Warning('No tiene permisos para agregar consumos negativos')
            record = super().create(values)
            if record.vlrUnitario == 0:
                if record.valorUnitario == 0:
                    raise Warning('No se permiten consumos de valor $0.0')
                else:
                    record.write({'vlrUnitario':record.valorUnitario})
            if record.producto_id.type == 'consu':
                raise Warning('No se puede cancelar orden de restaurante')
            ordenVenta = self.env['sale.order'].search(['&',('movimiento','=',record.movimiento_id.id),('state','=','sale')], limit=1)
            if not ordenVenta:
                raise Warning('Esta habitación no registra consumos')
            vendidas = 0
            for line in ordenVenta.order_line:
                if line.product_id.id == record.producto_id.product_variant_id.id:
                    vendidas += line.product_uom_qty
            cantidadPositiva = record.cantidad * -1
            if cantidadPositiva > vendidas:
                raise Warning('No se pueden devolver cantidades mayores a las ya registradas como consumos')
            # if record.producto_id.type == 'product':
                # TODO: Devolver cantidades de inventario
        else:
            record = super().create(values)
            if record.vlrUnitario == 0:
                if record.valorUnitario == 0:
                    raise Warning('No se permiten consumos de valor $0.0')
                else:
                    record.write({'vlrUnitario':record.valorUnitario})
            # if record.producto_id.type == 'product':
                # TODO: Revisar cantidades disponibles
            # elif record.producto_id.type == 'consu':
                # TODO: Explotar el inventario cuando sea restaurante
            ordenVenta = self.env['sale.order'].search(['&',('movimiento','=',record.movimiento_id.id),('state','=','sale')], limit=1)
            if not ordenVenta:
                valores = {
                    'partner_id' : cliente.id,
                    'movimiento' : record.movimiento_id.id
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
            if entrega.location_id.id == self.env.ref('stock.stock_location_stock').id:
                entrega.write({'location_id':record.lugar_id.id})
                for move in entrega.move_lines:
                    move.write({'location_id':record.lugar_id.id})
                for line in entrega.move_line_ids:
                    line.write({'location_id':record.lugar_id.id})
            if entrega.state == 'confirmed':
                for move in entrega.move_lines:
                    valoresLineaTransferencia = {
                        'company_id' : entrega.company_id.id,
                        'date' : fields.Datetime.now(),
                        'location_id' : entrega.location_id.id,
                        'location_dest_id' : entrega.location_dest_id.id,
                        'product_id' : record.producto_id.product_variant_id.id,
                        'product_uom_id' : record.producto_id.uom_id.id,
                        'qty_done' : move.product_uom_qty,
                        'picking_id' : entrega.id,
                        'move_id': move.id
                    }
                    lineaTransferencia = self.env['stock.move.line'].create(valoresLineaTransferencia)
                    if not lineaTransferencia:
                        raise Warning('No se pudo crear el movimiento de inventario')
                    entrega.button_validate()
        
        if record.llevaComanda:
            valoresComanda = {
                'producto_id' : record.producto_id.id,
                'cantidad' : record.cantidad,
                'descripcion' : record.textoComanda,
                'fecha' : fields.Datetime.now(),
                'habitacion' : record.habitacion.id,
                'movimiento_id' : record.movimiento_id.id,
                'vlrUnitario' : record.vlrUnitario
            }
            comanda = self.env['motgama.comanda'].sudo().create(valoresComanda)
            if not comanda:
                raise Warning('No se pudo crear la comanda')
            comanda.write({'nrocomanda':comanda.id})
            record.write({'comanda':comanda.id})
            # TODO: Imprimir comanda

        return record