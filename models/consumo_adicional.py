from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaFacturaConsumos(models.Model):
    _name = 'motgama.facturaconsumos'
    _description = 'Facturar consumos sin hospedaje'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre',compute='_compute_nombre',store=True)
    cliente_id = fields.Many2one(string='Cliente',comodel_name='res.partner',domain=[('customer','=',True)],default=lambda self: self._get_cliente())
    currency_id = fields.Many2one(comodel_name='res.currency',default=lambda self: self._get_currency())
    consumo_ids = fields.One2many(string='Consumos',comodel_name='motgama.lineafacturaconsumos',inverse_name='factura_id')
    valor_total = fields.Monetary(string='Valor total',compute='_compute_valor',store=True)
    factura_id = fields.Many2one(string='Factura', comodel_name='account.invoice')
    orden_venta = fields.Many2one(comodel_name='sale.order')
    active = fields.Boolean(string="Activo",default=True)

    @api.model
    def _get_currency(self):
        return self.env['res.company']._company_default_get('account.invoice').currency_id.id

    @api.model
    def _get_cliente(self):
        return self.env['res.partner'].search([('vat','=','1')]).id

    @api.depends('factura_id')
    def _compute_nombre(self):
        for record in self:
            if record.factura_id:
                record.nombre = record.factura_id.number
            else:
                record.nombre = '[Sin facturar]'

    @api.depends('consumo_ids')
    def _compute_valor(self):
        for record in self:
            valor = 0.0
            for consumo in record.consumo_ids:
                valor += consumo.vlrSubtotal
            record.valor_total = valor

    @api.multi
    def btn_facturar(self):
        self.ensure_one()
        if len(self.consumo_ids) == 0:
            raise Warning('Ingrese consumos para facturar')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardfacturaconsumos',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_recaudo_consumos').id,
            'target': 'new'
        }

    @api.multi
    def unlink(self):
        for record in self:
            if record.factura_id:
                raise Warning('No se pueden eliminar consumos ya facturados')
            else:
                return super().unlink()

class MotgamaLineaFacturaConsumos(models.Model):
    _name = 'motgama.lineafacturaconsumos'
    _description = 'Línea de factura de consumos sin hospedaje'

    currency_id = fields.Many2one(comodel_name='res.currency',default=lambda self: self._get_currency())
    factura_id = fields.Many2one(string='Factura sin hospedaje', comodel_name='motgama.facturaconsumos',required=True)
    producto_id = fields.Many2one(string='Producto',comodel_name='product.template',required=True)
    cantidad = fields.Float(string='Cantidad')
    valorUnitario = fields.Monetary(string='Valor Unitario',compute="_compute_valor")
    vlrUnitario = fields.Monetary(string='Valor Unitario')
    vlrSubtotal = fields.Monetary(string='Subtotal',compute='_compute_subtotal')
    permitecambiarvalor = fields.Boolean(string='Permite cambiar valor',default=False,compute="_compute_valor",store=True)

    @api.model
    def _get_currency(self):
        return self.env['res.company']._company_default_get('account.invoice').currency_id.id

    @api.depends('producto_id')
    def _compute_valor(self):
        for record in self:
            if record.producto_id:
                precio = record.producto_id.list_price
                if precio == 0.0:
                    record.permitecambiarvalor = True
                else:
                    record.permitecambiarvalor = False
                    record.valorUnitario = precio

    @api.depends('cantidad','vlrUnitario')
    def _compute_subtotal(self):
        for record in self:
            record.vlrSubtotal = record.vlrUnitario * record.cantidad

class MotgamaWizardFacturaConsumos(models.TransientModel):
    _name = 'motgama.wizardfacturaconsumos'
    _description = 'Wizard de recaudo de facturas de consumos adicionales'

    factura_id = fields.Many2one(comodel_name='motgama.facturaconsumos', default=lambda self: self._get_factura())
    deuda = fields.Float(string='Saldo restante',compute='_compute_deuda')
    total = fields.Float(string='Saldo total',default=lambda self: self._get_total())

    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner',domain="[('customer','=',True)]",default=lambda self: self._get_cliente())
    pagos = fields.Many2many(string='Recaudo',comodel_name='motgama.wizardpago')

    pago_prenda = fields.Boolean(string='Pago con prenda',default=False,compute='_compute_deuda')
    prendas_pendientes = fields.Many2many(string='Prendas pendientes por pagar',comodel_name='motgama.prendas',default=lambda self: self._get_pagadas())
    prendas_pagadas = fields.Many2many(string='Prendas pagadas',comodel_name='motgama.prendas',default=lambda self: self._get_pendientes())

    prenda_descripcion = fields.Char(string='Descripción de la prenda')
    prenda_valor = fields.Float(string='Valor estimado de la prenda')

    @api.model
    def _get_factura(self):
        return self.env.context['active_id']
    
    @api.model
    def _get_total(self):
        factura = self.env['motgama.facturaconsumos'].search([('id','=',self.env.context['active_id'])],limit=1)
        return factura.valor_total
    
    @api.model
    def _get_cliente(self):
        factura = self.env['motgama.facturaconsumos'].search([('id','=',self.env.context['active_id'])],limit=1)
        return factura.cliente_id.id

    @api.model
    def _get_pagadas(self):
        factura = self.env['motgama.facturaconsumos'].search([('id','=',self.env.context['active_id'])],limit=1)
        cliente = factura.cliente_id
        pagadas = []
        prendas = self.env['motgama.prendas'].search([('cliente_id','=',cliente.id),'|',('active','=',True),('active','=',False)])
        for prenda in prendas:
            if prenda.pagado:
                pagadas.append(prenda.id)
        return [(6,0,pagadas)]

    @api.model
    def _get_pendientes(self):
        factura = self.env['motgama.facturaconsumos'].search([('id','=',self.env.context['active_id'])],limit=1)
        cliente = factura.cliente_id
        pendientes = []
        prendas = self.env['motgama.prendas'].search([('cliente_id','=',cliente.id),'|',('active','=',True),('active','=',False)])
        for prenda in prendas:
            if not prenda.pagado:
                pendientes.append(prenda.id)
        return [(6,0,pendientes)]

    @api.depends('pagos.valor')
    def _compute_deuda(self):
        for recaudo in self:
            deuda = recaudo.total
            prenda = False
            for pago in recaudo.pagos:
                deuda -= pago.valor
                if pago.mediopago.lleva_prenda:
                    prenda = True
            recaudo.deuda = deuda
            recaudo.pago_prenda = prenda
    
    @api.multi
    def recaudar(self):
        self.ensure_one()

        valores = {'partner_id' : self.cliente.id}
        ordenVenta = self.env['sale.order'].create(valores)
        if not ordenVenta:
            raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
        ordenVenta.action_confirm()
        lugar = self.env['stock.location'].search([('recepcion','=',self.env.user.recepcion_id.id)],limit=1)
        if not lugar:
            raise Warning('No se encuentra la bodega de inventario ' + self.env.user.recepcion_id.nombre)
        for consumo in self.factura_id.consumo_ids:
            if consumo.vlrUnitario == 0:
                if consumo.valorUnitario == 0:
                    raise Warning('No se permiten consumos de valor $0.0')
                else:
                    consumo.sudo().write({'vlrUnitario':consumo.valorUnitario})
            if consumo.producto_id.type == 'product':
                producto = consumo.producto_id.product_variant_id
                cantDisponible = producto.with_context({'location': lugar.id}).qty_available
                # if cantDisponible < record.cantidad:
                    # TODO: Mostrar mensaje de no hay disponibilidad
            valoresLinea = {
                'customer_lead' : 0,
                'name' : consumo.producto_id.name,
                'order_id' : ordenVenta.id,
                'price_unit' : consumo.vlrUnitario,
                'product_uom_qty' : consumo.cantidad,
                'product_id' : consumo.producto_id.product_variant_id.id
            }
            nuevaLinea = self.env['sale.order.line'].create(valoresLinea)
            if not nuevaLinea:
                raise Warning('Error al registrar el consumo: No se pudo agregar el consumo a la orden de venta')
        if not self.env.user.recepcion_id:
            raise Warning('El usuario no tiene asignada una recepción')
        entregas = ordenVenta.picking_ids
        for entrega in entregas:
            if entrega.location_id.id == self.env.ref('stock.stock_location_stock').id:
                entrega.write({'location_id':lugar.id})
                for move in entrega.move_lines:
                    move.write({'location_id':lugar.id})
                for line in entrega.move_line_ids:
                    line.write({'location_id':lugar.id})
            if entrega.state == 'confirmed':
                for move in entrega.move_lines:
                    valoresLineaTransferencia = {
                        'company_id' : entrega.company_id.id,
                        'date' : fields.Datetime.now(),
                        'location_id' : entrega.location_id.id,
                        'location_dest_id' : entrega.location_dest_id.id,
                        'product_id' : move.product_id.product_variant_id.id,
                        'product_uom_id' : move.product_id.uom_id.id,
                        'qty_done' : move.product_uom_qty,
                        'picking_id' : entrega.id,
                        'move_id': move.id
                    }
                    lineaTransferencia = self.env['stock.move.line'].create(valoresLineaTransferencia)
                    if not lineaTransferencia:
                        raise Warning('No se pudo crear el movimiento de inventario')
                    entrega.button_validate()

        valoresPagos = []
        nroPrendas = 0
        valorPrenda = 0.0
        for pago in self.pagos:
            if pago.valor <= 0:
                raise Warning('No se admiten valores negativos o cero en los pagos')
            if pago.mediopago.tipo == 'prenda':
                valorPrenda = pago.valor
                if self.cliente.vat == '1':
                    raise Warning('Si se paga con prenda el cliente debe ser registrado con sus datos personales, no se admite "Cliente genérico"')
                nroPrendas += 1
                if nroPrendas > 1:
                    raise Warning('Solo se permite registrar un pago con prenda')
            if pago.mediopago.tipo == 'bono':
                raise Warning('El pago con bonos no está implementado')
                # TODO: Implementar bonos
            valores = {
                'cliente_id': self.cliente.id,
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'descripcion': pago.descripcion
            }
            valoresPagos.append(valores)

        ordenVenta.action_invoice_create(final=True)
        for invoice in ordenVenta.invoice_ids:
            factura = invoice
            break
        if not factura:
            raise Warning('No se pudo crear la factura')
        factura.write({'es_hospedaje':True})
        factura.action_invoice_open()
        diario = self.env['account.journal'].search([('company_id','=',factura.company_id.id),('type','=','cash')],limit=1)
        valorPagado = self.total
        valoresPayment = {
            'amount': valorPagado,
            'currency_id': diario.company_id.currency_id.id,
            'invoice_ids': [(4,factura.id)],
            'journal_id': diario.id,
            'payment_date': fields.Datetime().now(),
            'payment_type': 'inbound',
            'payment_method_id': 1,
            'partner_type': 'customer'
        }
        payment = self.env['account.payment'].create(valoresPayment)
        if not payment:
            raise Warning('No fue posible sentar el registro del pago')
        payment.post()

        valoresRecaudo = {
            'cliente': self.cliente.id,
            'factura': factura.id,
            'total_pagado': self.total
        }
        if self.pago_prenda:
            valoresPrenda = {
                'factura': factura.id,
                'cliente_id': self.cliente.id,
                'descripcion': self.prenda_descripcion,
                'valorprenda': self.prenda_valor,
                'valordeuda': valorPrenda
            }
            nuevaPrenda = self.env['motgama.prendas'].create(valoresPrenda)
            if not nuevaPrenda:
                raise Warning('No se pudo registrar la prenda')
            valoresRecaudo.update({'prenda': nuevaPrenda.id})
        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('No se pudo registrar el recaudo')

        for valores in valoresPagos:
            valores.update({'recaudo':nuevoRecaudo.id})
            nuevoPago = self.env['motgama.pago'].create(valores)
            if not nuevoPago:
                raise Warning('No se pudo guardar la información del pago')
        
        self.factura_id.write({'factura_id':factura.id})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_mode': 'form',
            'res_id': factura.id,
            'target': 'current'
        }