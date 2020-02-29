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
    es_hospedaje = fields.Boolean(string='Servicio de hospedaje',default=False)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    es_hospedaje = fields.Boolean(string='Servicio de hospedaje',default=False)

    @api.onchange('categ_id')
    def _onchange_categ(self):
        for record in self:
            if record.categ_id:
                record.es_hospedaje = record.categ_id.es_hospedaje

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
                if cantDisponible < record.cantidad:
                    message = 'No se registra cantidad suficiente de ' + record.producto_id.name + '. Va a vender ' + str(int(record.cantidad)) + ' unidades y tiene ' + str(cantDisponible) + ' unidades en ' + record.lugar_id.name
                    self.env.user.notify_info(message=message,title='No hay suficiente cantidad',sticky=False)
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

class MotgamaWizardConsumos(models.TransientModel):
    _name = 'motgama.wizard.consumos'
    _description = 'Wizard Consumos'

    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    producto_id = fields.Many2one(string='Producto (Cod. Barras, Nombre, Código)',comodel_name='product.template')
    lugar_id = fields.Many2one(string='Recepción',comodel_name='stock.location')
    linea_ids = fields.Many2many(string='Consumos',comodel_name='motgama.wizard.consumos.line')
    total_prods = fields.Integer(string='Total items',compute='_compute_items')
    total_consumos = fields.Float(string='Total consumos',compute='_compute_total')
    consumo_ids = fields.Many2many(string='Consumos anteriores',comodel_name='motgama.consumo',default=lambda self: self._get_consumos())

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.model
    def _get_consumos(self):
        hab = self.env['motgama.flujohabitacion'].browse(self.env.context['active_id'])
        ids = [consumo.id for consumo in hab.consumos]
        return [(6,0,ids)]
    
    @api.onchange('habitacion_id')
    def _onchange_habitacion(self):
        for record in self:
            if record.habitacion_id:
                record.lugar_id = self.env['stock.location'].search([('recepcion','=',record.habitacion_id.recepcion.id)],limit=1)
    
    @api.onchange('producto_id')
    def _onchange_producto(self):
        for record in self:
            if record.producto_id and record.habitacion_id:
                movimiento = record.habitacion_id.ultmovimiento
                lista = movimiento.listaprecioproducto
                precioLista = self.env['product.pricelist.item'].search(['&',('pricelist_id','=',lista.id),('product_tmpl_id','=',record.producto_id.id)], limit=1)
                if not precioLista:
                    precio = record.producto_id.list_price
                else:
                    precio = precioLista.fixed_price

                if precio == 0.0:
                    permitecambiarvalor = True
                    valor = 0
                else:
                    permitecambiarvalor = False
                    valor = precio
                valores = {
                    'producto_id': record.producto_id.id,
                    'lugar_id': record.lugar_id.id,
                    'vlrUnitario': valor,
                    'vlrUnitario_save': valor,
                    'cantidad': 1,
                    'cambiar_valor': permitecambiarvalor,
                    'lleva_comanda': record.producto_id.categ_id.llevaComanda
                }
                record.linea_ids = [(0,0,valores)]
                record.producto_id = None
    
    @api.depends('linea_ids.cantidad')
    def _compute_items(self):
        for record in self:
            suma = 0
            for linea in record.linea_ids:
                suma += linea.cantidad
            record.total_prods = suma
    
    @api.depends('linea_ids.vlrSubtotal')
    def _compute_total(self):
        for record in self:
            suma = 0
            for linea in record.linea_ids:
                suma += linea.vlrSubtotal
            record.total_consumos = suma

    @api.multi
    def agregar_consumos(self):
        self.ensure_one()
        
        for linea in self.linea_ids:
            valores = {
                'recepcion': self.habitacion_id.recepcion.id,
                'llevaComanda': linea.lleva_comanda,
                'textoComanda': linea.comanda,
                'habitacion': self.habitacion_id.id,
                'movimiento_id': self.habitacion_id.ultmovimiento.id,
                'producto_id': linea.producto_id_save.id,
                'cantidad': linea.cantidad,
                'valorUnitario': linea.vlrUnitario_save,
                'vlrUnitario': linea.vlrUnitario_save,
                'vlrSubtotal': linea.vlrSubtotal_save,
                'lugar_id': linea.lugar_id.id,
                'asigna_uid': self.env.user.id,
                'permitecambiarvalor': linea.cambiar_valor
            }
            consumo = self.env['motgama.consumo'].create(valores)
            if not consumo:
                raise Warning('No se pudo registrar los consumos')
        self.habitacion_id.refresh_views()
        return True

class MotgamaLineaConsumos(models.TransientModel):
    _name = 'motgama.wizard.consumos.line'
    _description = 'Línea Wizard Consumos'

    producto_id = fields.Many2one(string='Producto',comodel_name='product.template')
    producto_id_save = fields.Many2one(string='Producto',comodel_name='product.template',compute="_producto_id_save",store=True)
    lugar_id = fields.Many2one(string='Recepción',comodel_name='stock.location')
    vlrUnitario = fields.Float(string='Valor Unitario')
    vlrUnitario_save = fields.Float(string='Valor Unitario')
    cantidad = fields.Integer(string='Cantidad')
    vlrSubtotal = fields.Float(string='Subtotal',compute='_compute_subtotal',store=True)
    vlrSubtotal_save = fields.Float(string='Subtotal',compute='_vlrSubtotal_save',store=True)
    cambiar_valor = fields.Boolean(string='Puede cambiar valor',default=False)
    lleva_comanda = fields.Boolean(string='Lleva comanda',default=False)
    comanda = fields.Text(string='Comanda',default='')

    @api.depends('vlrUnitario_save','cantidad')
    def _compute_subtotal(self):
        for record in self:
            if record.vlrUnitario_save and record.cantidad:
                record.vlrSubtotal = record.vlrUnitario_save * record.cantidad
    
    @api.depends('producto_id')
    def _producto_id_save(self):
        for record in self:
            if self.producto_id:
                record.producto_id_save = record.producto_id
    
    @api.depends('vlrSubtotal')
    def _vlrSubtotal_save(self):
        for record in self:
            if self.vlrSubtotal:
                record.vlrSubtotal_save = record.vlrSubtotal

    @api.model
    def create(self,values):
        if not 'vlrUnitario_save' in values:
            values['vlrUnitario_save'] = values['vlrUnitario']
        return super().create(values)

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_consumos(self):
        self.ensure_one()

        return {
            'name': 'Agregar consumos a la habitación ' + self.codigo,
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.consumos',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.form_wizard_consumo').id,
            'target': 'new'
        }