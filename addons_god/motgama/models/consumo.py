from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import Warning

class MotgamaConsumo(models.Model):
#    Fields: Consumos del Bar en cualquiera de las recepciones: Creado: Junio 07 del 2019
    _name = 'motgama.consumo' 
    _description = 'Consumos'
    _inherit = 'base'
    # 19 jun se cambia por habitacion para despues realizar un autoguardado
    recepcion = fields.Many2one(comodel_name='motgama.recepcion',default=lambda self: self.env.user.recepcion_id.id)
    consecutivo =  fields.Float(string='Total $')
    llevaComanda = fields.Boolean(string='¿Lleva Comanda?',default=False)
    textoComanda = fields.Text(string='Comanda')
    comanda = fields.Many2one(string='Comanda asociada',comodel_name='motgama.comanda')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',ondelete='set null')
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',compute='_compute_movimiento',store=True)
    producto_id = fields.Many2one(string='Producto',comodel_name='product.template',ondelete='set null',required=True)
    cantidad = fields.Float(string='Cantidad',required=True)
    valorUnitario = fields.Float(string='Valor Unitario',compute='_compute_valorUnitario')                                                                                   #P7.0.4R
    vlrUnitario = fields.Float(string='Valor Unitario')
    vlrSubtotal = fields.Float(string='Subtotal $',compute="_compute_vlrsubtotal",store = True)
    lugar_id = fields.Many2one(string='Bodega de Inventario',comodel_name='stock.location',ondelete='set null',store=True)
    estado = fields.Char(string='estado')
    active = fields.Boolean(string='Activo?',default=True)
    asigna_uid = fields.Many2one(comodel_name='res.users',string='Usuario responsable',default=lambda self: self.env.user.id)
    permitecambiarvalor = fields.Boolean(string='Permite cambiar valor',default=False,compute="_compute_valorUnitario",store=True)
    es_adicional = fields.Boolean(string="Facturado aparte",default=False)

    @api.onchange('producto_id')
    def onchange_producto(self):
        for record in self:
            if record.producto_id:
                record.llevaComanda = record.producto_id.categ_id.llevaComanda

    @api.depends('habitacion')
    def _compute_movimiento(self):
        for record in self:
            record.movimiento_id = record['habitacion'].ultmovimiento

    @api.onchange('habitacion')
    def onchange_habitacion(self):
        for record in self:
            if record.habitacion:
                lugar = self.env['stock.location'].search(['&',('recepcion','=',record.habitacion.recepcion.id),('permite_consumo','=',True)],limit=1)
                if not lugar:
                    raise Warning('No existe lugar de inventario para la recepción: ' + record.habitacion.recepcion.nombre)
                record.lugar_id = lugar.id

    @api.depends('vlrUnitario')
    def _compute_vlrsubtotal(self):
        for record in self:
            record['vlrSubtotal'] = record.vlrUnitario * record.cantidad

    @api.depends('producto_id')
    def _compute_valorUnitario(self):
        for record in self:
            if record.producto_id:
                movimiento = self.env['motgama.movimiento'].search([('id','=',record.movimiento_id.id)], limit=1)
                lista = movimiento.listaprecioproducto
                precioLista = self.env['product.pricelist.item'].sudo().search(['&',('pricelist_id','=',lista.id),('product_tmpl_id','=',record.producto_id.id)], limit=1)
                if not precioLista:
                    precio = record.producto_id.list_price
                else:
                    precio = precioLista.fixed_price
                if precio == 0.0:
                    record.permitecambiarvalor = True
                else:
                    record.permitecambiarvalor = False
                    record.valorUnitario = precio
    
    @api.onchange('valorUnitario')
    def _onchange_valorUnitario(self):
        for record in self:
            if record.valorUnitario:
                if record.valorUnitario != 0:
                    record.vlrUnitario = record.valorUnitario

    @api.model
    def create(self,values):
        if 'es_adicional' in values and values['es_adicional']:
            return super().create(values)
        cliente = self.env['res.partner'].sudo().search([('vat','=','1')], limit=1)
        if not cliente:
            raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')
        esNegativo = False
        if values['cantidad'] == 0:
            raise Warning('Debe especificar una cantidad mayor a cero')
        elif values['cantidad'] < 0:
            if not self.env.ref('motgama.motgama_consumo_negativo') in self.env.user.permisos:
               raise Warning('No tiene permisos para agregar consumos negativos')
            record = super().create(values)
            if record.vlrUnitario == 0:
                if record.valorUnitario == 0:
                    raise Warning('No se permiten consumos de valor $0.0')
                else:
                    record.sudo().write({'vlrUnitario':record.valorUnitario})
            if record.producto_id.type == 'consu':
                raise Warning('No se puede cancelar orden de restaurante')
            ordenVenta = self.env['sale.order'].sudo().search(['&',('movimiento','=',record.movimiento_id.id),('state','=','sale')], limit=1)
            if not ordenVenta:
                raise Warning('Esta habitación no registra consumos')
            vendidas = 0
            for line in ordenVenta.order_line:
                if line.product_id.id == record.producto_id.product_variant_id.id:
                    vendidas += line.product_uom_qty
            cantidadPositiva = record.cantidad * -1
            if cantidadPositiva > vendidas:
                raise Warning('No se pueden devolver cantidades mayores a las ya registradas como consumos')
            if record.producto_id.type == 'product' and len(record.producto_id.bom_ids) == 0:
                origen = self.env['stock.location'].sudo().search([('usage','=','customer')],limit=1)
                tipo_operacion = self.env['stock.picking.type'].sudo().search([('code','=','incoming')],limit=1)
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
                transferencia = self.env['stock.picking'].sudo().create(valoresTransferencia)
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
                lineaTransferencia = self.env['stock.move'].sudo().create(valoresLinea)
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
                move_line = self.env['stock.move.line'].sudo().create(valores_move_line)
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
            if len(record.producto_id.bom_ids) > 0:
                bom_id = self.env['mrp.bom'].sudo().search([('product_tmpl_id','=',record.producto_id.id)],limit=1)
                if bom_id:
                    valoresProd = {
                        'product_id': record.producto_id.product_variant_id.id,
                        'date_planned_start': fields.Datetime().now(),
                        'product_qty': record.cantidad,
                        'product_uom_id': record.producto_id.uom_id.id,
                        'bom_id': bom_id.id
                    }
                    prod = self.env['mrp.production'].sudo().create(valoresProd)
                    if not prod:
                        raise Warning('No se pudo registrar orden de restaurante')
                    prod.action_assign()
                    if prod.state == 'confirmed' and prod.availability not in ['assigned','none']:
                        message = 'No se registra cantidad suficiente de ingredientes para ' + str(int(record.cantidad)) + ' unidad(es) de ' + record.producto_id.name
                        self.env.user.notify_info(message=message,title='Problema con ingredientes',sticky=False)
                    valoresProduce = {
                        'serial': False,
                        'production_id': prod.id,
                        'product_id': record.producto_id.product_variant_id.id,
                        'product_qty': record.cantidad,
                        'product_uom_id': record.producto_id.uom_id.id
                    }
                    produce = self.env['mrp.product.produce'].sudo().create(valoresProduce)
                    if not produce:
                        raise Warning('No se pudo registrar orden de restaurante')
                    produce._onchange_product_qty()
                    produce.do_produce()
                    prod.button_mark_done()
                    record.sudo().write({'lugar_id': prod.location_dest_id.id})
            if record.producto_id.type == 'product':
                producto = record.producto_id.product_variant_id
                cantDisponible = producto.with_context({'location': record.lugar_id.id}).qty_available
                if cantDisponible < record.cantidad:
                    message = 'No se registra cantidad suficiente de ' + record.producto_id.name + '. Va a vender ' + str(int(record.cantidad)) + ' unidades y tiene ' + str(cantDisponible) + ' unidades en ' + record.lugar_id.name
                    self.env.user.notify_info(message=message,title='No hay suficiente cantidad',sticky=False)
            ordenVenta = self.env['sale.order'].sudo().search(['&',('movimiento','=',record.movimiento_id.id),('state','=','sale')], limit=1)
            if not ordenVenta:
                valores = {
                    'partner_id' : cliente.id,
                    'movimiento' : record.movimiento_id.id
                }
                ordenVenta = self.env['sale.order'].sudo().create(valores)
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
        nuevaLinea = self.env['sale.order.line'].sudo().create(valoresLinea)
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
            if entrega.state in ['confirmed','assigned']:
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
                    lineaTransferencia = self.env['stock.move.line'].sudo().create(valoresLineaTransferencia)
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

        hab = self.env['motgama.habitacion'].search([('codigo','=',record.habitacion.codigo)],limit=1)
        if not hab:
            raise Warning('Error al consultar la habitación')
        
        cod_adic = self.env['motgama.parametros'].search([('codigo','=','PERSADIC')],limit=1)
        if not cod_adic:
            raise Warning('Error: no se ha definido el parámetro "PERSADIC"')
        if record.producto_id.default_code == cod_adic.valor and hab.inmotica:
            valoresInmotica = {
                'habitacion': self.habitacion.codigo,
                'mensaje': 'evento',
                'evento': 'Ingresa persona adicional'
            }
            mensajeInmotica = self.env['motgama.inmotica'].create(valoresInmotica)
            if not mensajeInmotica:
                raise Warning('Error al registrar inmótica')
        
        self.refresh_views()

        return record