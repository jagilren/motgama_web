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
        esNegativo = False
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
                    record.sudo().write({'vlrUnitario':record.valorUnitario})
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
            if record.producto_id.type == 'product':
                origen = self.env['stock.location'].search([('usage','=','customer')],limit=1)
                tipo_operacion = self.env['stock.picking.type'].search([('code','=','incoming')],limit=1)
                valoresTransferencia = {
                    'company_id': ordenVenta.company_id.id,
                    'location_dest_id': record.lugar_id.id,
                    'location_id': origen.id,
                    'origin': ordenVenta.name,
                    'move_type': 'direct',
                    'picking_type_id': tipo_operacion.id,
                    'product_id': record.producto_id.product_variant_id.id,
                    'sale_id': ordenVenta.id
                }
                transferencia = self.env['stock.picking'].create(valoresTransferencia)
                if not transferencia:
                    raise Warning('No se pudo crear la transferencia de inventario')
                valoresLinea = {
                    'company_id': transferencia.company_id.id,
                    'date': fields.Datetime().now(),
                    'date_expected': fields.Datetime().now(),
                    'location_dest_id': transferencia.location_dest_id.id,
                    'location_id': transferencia.location_id.id,
                    'name': 'Retorno de ' + ordenVenta.name,
                    'procure_method': 'make_to_stock',
                    'product_id': record.producto_id.product_variant_id.id,
                    'product_uom': record.producto_id.product_variant_id.uom_id.id,
                    'product_uom_qty': cantidadPositiva,
                    'picking_id': transferencia.id
                }
                lineaTransferencia = self.env['stock.move'].create(valoresLinea)
                if not lineaTransferencia:
                    raise Warning('No se pudo crear la transferencia de inventario')
                transferencia.action_confirm()
                valores_move_line = {
                    'date': fields.Datetime().now(),
                    'location_dest_id': transferencia.location_dest_id.id,
                    'location_id': transferencia.location_id.id,
                    'product_id': transferencia.product_id.id,
                    'product_uom_id': record.producto_id.product_variant_id.uom_id.id,
                    'product_uom_qty': cantidadPositiva,
                    'picking_id': transferencia.id,
                    'move_id': lineaTransferencia.id,
                    'qty_done': cantidadPositiva
                }
                move_line = self.env['stock.move.line'].create(valores_move_line)
                if not move_line:
                    raise Warning('No se pudo crear la transferencia de inventario')
                transferencia.button_validate()
                esNegativo = True
        else:
            record = super().create(values)
            if record.vlrUnitario == 0:
                if record.valorUnitario == 0:
                    raise Warning('No se permiten consumos de valor $0.0')
                else:
                    record.sudo().write({'vlrUnitario':record.valorUnitario})
            if record.producto_id.type == 'product':
                producto = record.producto_id.product_variant_id
                cantDisponible = producto.with_context({'location': record.lugar_id.id}).qty_available
                # if cantDisponible < record.cantidad:
                    # TODO: Mostrar mensaje de no hay disponibilidad
            # TODO: Explotar el inventario cuando sea restaurante o bar
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

        if esNegativo:
            move_line.write({'sale_line_id':nuevaLinea.id})

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
                'recepcion_id' : record.habitacion.recepcion.id,
                'usuario_id' : self.env.user.id
            }
            comanda = self.env['motgama.comanda'].sudo().create(valoresComanda)
            if not comanda:
                raise Warning('No se pudo crear la comanda')
            comanda.write({'nrocomanda':comanda.id})
            record.sudo().write({'comanda':comanda.id})
        
        cod_adic = self.env['motgama.parametros'].search([('codigo','=','PERSADIC')],limit=1)
        if record.producto_id.default_code == cod_adic.valor:
            valoresInmotica = {
                'habitacion': self.codigo,
                'mensaje': 'evento',
                'evento': 'Ingresa persona adicional'
            }
            mensajeInmotica = self.env['motgama.inmotica'].create(valoresInmotica)
            if not mensajeInmotica:
                raise Warning('Error al registrar inmótica')
        
        self.refresh_views()

        return record