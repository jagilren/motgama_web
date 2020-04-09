from odoo import models, fields, api
from odoo.exceptions import Warning

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fecha = fields.Datetime(string='Fecha y hora')
    es_hospedaje = fields.Boolean(default=False)
    habitacion_id = fields.Many2one(string='Habitación',comodel_name="motgama.flujohabitacion")
    recaudo = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo')
    asignafecha = fields.Datetime(string="Ingreso")
    liquidafecha = fields.Datetime(string="Salida")
    lleva_prenda = fields.Boolean(string='Lleva prenda',default=False)
    prenda_id = fields.Many2one(string='Prenda',comodel_name='motgama.prendas')

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_recaudar(self):
        self.ensure_one()
        if not self.env.user.motgama_recauda_habitacion:
            raise Warning('No tiene permitido recaudar habitaciones, contacte al administrador')

        if not self.puede_recaudar:
            prestados = self.env['motgama.objprestados'].search([('habitacion_id','=',self.id)])
            if prestados:
                return {
                    'name': 'Hay objetos prestados',
                    'type': 'ir.actions.act_window',
                    'res_model': 'motgama.confirm.prestados',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('motgama.form_confirm_prestados').id,
                    'target': 'new'
                }
            else:
                self.write({'puede_recaudar': True})
        self.write({'puede_recaudar': False})
        return {
            'name': 'Recaudar habitación',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardrecaudo',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.motgama_wizard_recaudo').id,
            'target': 'new',
            'context': {'current_id': self.id}
        }
    
    @api.multi
    def button_factura(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_mode': 'form',
            'view_id': self.env.ref('account.invoice_form').id,
            'res_id': self.factura.id,
            'target': 'current'
        }

class MotgamaWizardRecaudo(models.TransientModel):
    _name = 'motgama.wizardrecaudo'
    _description = 'Wizard para recaudo de habitaciones'

    movimiento = fields.Many2one(comodel_name='motgama.movimiento',default=lambda self: self._compute_movimiento())

    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._compute_habitacion())
    deuda = fields.Float(string='Saldo restante',compute='_compute_deuda')
    total = fields.Float(string='Saldo total',default=lambda self: self._compute_total())

    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner',domain="[('customer','=',True)]",default=lambda self: self._compute_cliente())
    pagos = fields.Many2many(string='Recaudo',comodel_name='motgama.wizardpago',default=lambda self: self._get_abonos())
    pago_prenda = fields.Boolean(string='Pago con prenda',default=False,compute='_compute_deuda')
    prendas_pendientes = fields.Many2many(string='Prendas pendientes por pagar',comodel_name='motgama.prendas',compute='_compute_prendas')
    prendas_pagadas = fields.Many2many(string='Prendas pagadas',comodel_name='motgama.prendas',compute='_compute_prendas')

    prenda_descripcion = fields.Char(string='Descripción de la prenda')
    prenda_valor = fields.Float(string='Valor estimado de la prenda')
    abonado = fields.Float(string="Valor abonado",compute='_compute_abonado')

    @api.model
    def _compute_habitacion(self):
        flujo_id = self.env.context['current_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
        return flujo.id

    @api.model
    def _compute_movimiento(self):
        flujo_id = self.env.context['current_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
        return flujo.ultmovimiento.id

    @api.model
    def _compute_cliente(self):
        cliente = self.env['res.partner'].search([('vat','=','1')],limit=1)
        if not cliente:
            raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')
        return cliente.id

    @api.model
    def _compute_total(self):
        flujo_id = self.env.context['current_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
        ordenVenta = self.env['sale.order'].search([('movimiento','=',flujo.ultmovimiento.id),('state','=','sale')],limit=1)
        return ordenVenta.amount_total
    
    @api.model
    def _get_abonos(self):
        flujo_id = self.env.context['current_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
        movimiento = flujo.ultmovimiento
        mediopago = self.env.ref('motgama.mediopago_abono')
        totalAbono = 0.0
        for recaudo in movimiento.recaudo_ids:
            totalAbono += recaudo.total_pagado
        if totalAbono > 0:
            valoresPago = {
                'mediopago': mediopago.id,
                'valor': totalAbono
            }
            return [(0,0,valoresPago)]
        return []

    @api.depends('movimiento')
    def _compute_abonado(self):
        for record in self:
            if record.movimiento:
                totalAbono = 0.0
                for recaudo in record.movimiento.recaudo_ids:
                    totalAbono += recaudo.total_pagado
                record.abonado = totalAbono
            
        
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

    @api.depends('cliente')
    def _compute_prendas(self):
        for recaudo in self:
            pagadas = []
            pendientes = []
            if recaudo.cliente:
                prendas = self.env['motgama.prendas'].search([('cliente_id','=',recaudo.cliente.id),'|',('active','=',True),('active','=',False)])
                for prenda in prendas:
                    if prenda.pagado:
                        pagadas.append(prenda.id)
                    else:
                        pendientes.append(prenda.id)
                recaudo.prendas_pagadas = [(6,0,pagadas)]
                recaudo.prendas_pendientes = [(6,0,pendientes)]
    
    @api.multi
    def recaudar(self):
        self.ensure_one()
        if self.deuda > 0:
            raise Warning('La cuenta no ha sido saldada')
        elif self.deuda < 0:
            raise Warning('El valor pagado es mayor al valor de la cuenta')
        
        valoresPagos = []
        nroPrendas = 0
        valorPrenda = 0.0

        tiene_recaudo = False
        if len(self.movimiento.recaudo_ids) > 0:
            tiene_recaudo = True
        tiene_abono = False
        abono = 0.0
        for pago in self.pagos:
            if pago.valor <= 0:
                raise Warning('No se admiten valores negativos o cero en los pagos')
            if pago.mediopago.tipo == 'prenda':
                valorPrenda = pago.valor
                if self.cliente.vat == '1':
                    raise Warning('Si se paga con prenda el cliente debe ser registrado con sus datos personales, no se admite el cliente genérico')
                nroPrendas += 1
                if nroPrendas > 1:
                    raise Warning('Solo se permite registrar un pago con prenda')
            elif pago.mediopago.tipo == 'pase':
                if not self.env.user.motgama_pase_cortesia:
                    raise Warning('Error: No tiene permiso para registrar pago con Pase/Cortesía')
            elif pago.mediopago.tipo == 'abono':
                tiene_abono = True
                abono = pago.valor
            valores = {
                'movimiento_id': self.movimiento.id,
                'cliente_id': self.cliente.id,
                'mediopago': pago.mediopago.id,
                'valor': pago.valor
            }
            valoresPagos.append(valores)
        if tiene_recaudo:
            if not tiene_abono:
                raise Warning('No debe eliminar el abono de la sección de pagos')
            if self.abonado != abono:
                raise Warning('No debe modificar el valor abonado en la sección de pagos')

        ordenVenta = self.env['sale.order'].search([('movimiento','=',self.movimiento.id),('state','=','sale')],limit=1)
        if not ordenVenta:
            raise Warning('Error al recaudar: La habitación no fue recaudada correctamente')
        ordenVenta.write({'partner_id':self.cliente.id})
        ordenVenta.action_invoice_create(final=True)
        for invoice in ordenVenta.invoice_ids:
            factura = invoice
            break
        if not factura:
            raise Warning('No se pudo crear la factura')
        valoresFactura = {
            'partner_id':self.cliente.id,
            'es_hospedaje':True,
            'habitacion_id':self.habitacion.id,
            'company_id':ordenVenta.company_id.id,
            'asignafecha':ordenVenta.asignafecha,
            'liquidafecha':ordenVenta.liquidafecha,
            'fecha':fields.Datetime().now()
        }
        factura.write(valoresFactura)
        factura.action_invoice_open()
        for recaudo in self.movimiento.recaudo_ids:
            for pago in recaudo.pagos:
                if pago.mediopago.tipo in ['prenda','abono']:
                    continue
                if not pago.pago_id.journal_id.update_posted:
                    pago.pago_id.journal_id.sudo().write({'update_posted':True})
                pago.pago_id.sudo().cancel()
                pago.pago_id.sudo().action_draft()
                pago.pago_id.sudo().write({'invoice_ids': [(4,factura.id)]})
                pago.pago_id.sudo().post()
        for pago in self.pagos:
            if pago.mediopago.tipo in ['prenda','abono']:
                continue
            valoresPayment = {
                'amount': pago.valor,
                'currency_id': pago.mediopago.diario_id.company_id.currency_id.id,
                'invoice_ids': [(4,factura.id)],
                'journal_id': pago.mediopago.diario_id.id,
                'payment_date': fields.Datetime().now(),
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'partner_type': 'customer'
            }
            payment = self.env['account.payment'].create(valoresPayment)
            if not payment:
                raise Warning('No fue posible sentar el registro del pago')
            payment.post()
            for valores in valoresPagos:
                if valores['mediopago'] == pago.mediopago.id and valores['valor'] == pago.valor:
                    valores['pago_id'] = payment.id
        
        valoresRecaudo = {
            'movimiento_id': self.movimiento.id,
            'habitacion': self.habitacion.id,
            'cliente': self.cliente.id,
            'factura': factura.id,
            'total_pagado': self.total,
            'valor_pagado': self.total - valorPrenda,
            'tipo_recaudo': 'habitaciones',
            'recepcion_id': self.env.user.recepcion_id.id
        }
        if self.pago_prenda:
            valoresPrenda = {
                'habitacion_id': self.habitacion.id,
                'movimiento_id': self.movimiento.id,
                'factura': factura.id,
                'tipovehiculo': self.movimiento.tipovehiculo,
                'placa': self.movimiento.placa_vehiculo,
                'cliente_id': self.cliente.id,
                'descripcion': self.prenda_descripcion,
                'valorprenda': self.prenda_valor,
                'valordeuda': valorPrenda,
                'nroprenda': 'Nuevo'
            }
            nuevaPrenda = self.env['motgama.prendas'].create(valoresPrenda)
            if not nuevaPrenda:
                raise Warning('No se pudo registrar la prenda')
            valoresRecaudo.update({'prenda': nuevaPrenda.id})
            factura.update({'lleva_prenda':True,'prenda_id':nuevaPrenda.id})
        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('No se pudo registrar el recaudo')
        factura.write({'recaudo':nuevoRecaudo.id})

        for valores in valoresPagos:
            valores.update({'recaudo':nuevoRecaudo.id})
            nuevoPago = self.env['motgama.pago'].create(valores)
            if not nuevoPago:
                raise Warning('No se pudo guardar la información del pago')
        
        self.habitacion.write({'estado':'RC','factura':factura.id,'notificar':True})
        self.movimiento.write({
            'recaudafecha':fields.Datetime().now(),
            'recauda_uid':self.env.user.id,
            'factura': factura.id
            })
        
        consumos = self.env['motgama.consumo'].search([('movimiento_id','=',self.movimiento.id)])
        for consumo in consumos:
            consumo.sudo().write({'active': False})

        prestados = self.env['motgama.objprestados'].search([('habitacion_id','=',self.habitacion.id)],limit=1)
        if prestados:
            for prestado in prestados:
                prestado.write({'active':False})
        
        hab = self.env['motgama.habitacion'].search([('codigo','=',self.habitacion.codigo)],limit=1)
        if not hab:
            raise Warning('Error al cargar la habitación')
        if hab.inmotica:
            valoresInmotica = {
                'habitacion': self.habitacion.codigo,
                'mensaje': 'salida',
                'evento': 'Habitación recaudada'
            }
            mensajeInmotica = self.env['motgama.inmotica'].create(valoresInmotica)
            if not mensajeInmotica:
                raise Warning('Error al registrar inmótica')

        return True

class MotgamaWizardPago(models.TransientModel):
    _name = 'motgama.wizardpago'
    _description = 'Wizard Pagos'

    mediopago = fields.Many2one(string='Medio de Pago',comodel_name='motgama.mediopago',required=True)
    valor =  fields.Float(string='Valor a pagar',required=True)