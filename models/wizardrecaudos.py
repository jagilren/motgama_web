from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardRecaudo(models.TransientModel):
    _name = 'motgama.wizardrecaudo'
    _description = 'Wizard para recaudo de habitaciones'

    movimiento = fields.Many2one(comodel_name='motgama.movimiento',default=lambda self: self._compute_movimiento())

    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._compute_habitacion())
    deuda = fields.Float(string='Saldo restante',compute='_compute_deuda')
    total = fields.Float(string='Saldo total',default=lambda self: self._compute_total())

    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner',domain="[('customer','=',True)]",default=lambda self: self._compute_cliente())
    pagos = fields.Many2many(string='Recaudo',comodel_name='motgama.wizardpago')
    pago_prenda = fields.Boolean(string='Pago con prenda',default=False,compute='_compute_deuda')
    prendas_pendientes = fields.Many2many(string='Prendas pendientes por pagar',comodel_name='motgama.prendas',compute='_compute_prendas')
    prendas_pagadas = fields.Many2many(string='Prendas pagadas',comodel_name='motgama.prendas',compute='_compute_prendas')

    prenda_descripcion = fields.Char(string='Descripción de la prenda')
    prenda_valor = fields.Float(string='Valor de la prenda')

    valores_pagos = []

    @api.model
    def _compute_habitacion(self):
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
        return flujo.id

    @api.model
    def _compute_movimiento(self):
        flujo_id = self.env.context['active_id']
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
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
        ordenVenta = self.env['sale.order'].search([('movimiento','=',flujo.ultmovimiento.id),('state','=','sale')],limit=1)
        return ordenVenta.amount_total

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
                prendas = self.env['motgama.prendas'].search([('cliente_id','=',recaudo.cliente.id)])
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
                'movimiento_id': self.movimiento.id,
                'cliente_id': self.cliente.id,
                'mediopago': pago.mediopago.id,
                'valor': pago.valor,
                'descripcion': pago.descripcion
            }
            valoresPagos.append(valores)

        # TODO: Crear y confirmar factura
        ordenVenta = self.env['sale.order'].search([('movimiento','=',self.movimiento.id),('state','=','sale')],limit=1)
        if not ordenVenta:
            raise Warning('Error al recaudar: La habitación no fue recaudada correctamente')
        ordenVenta.action_invoice_create()
        for invoice in ordenVenta.invoice_ids:
            factura = invoice
            break
        if not factura:
            raise Warning('No se pudo crear la factura')
        factura.action_invoice_open()
        diario = self.env['account.journal'].search([('company_id','=',factura.company_id.id),('type','=','cash')],limit=1)
        valoresPayment = {
            'amount': self.total,
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
            'movimiento_id': self.movimiento.id,
            'habitacion': self.habitacion.id,
            'cliente': self.cliente.id,
            'factura': factura.id,
            'total_pagado': self.total
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
        
        self.habitacion.write({'estado':'RC'})
        self.movimiento.write({
            'recaudafecha':fields.Datetime().now(),
            'recauda_uid':self.env.user.id,
            'factura': factura.id
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_mode': 'form',
            'res_id': factura.id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}}
        }
        


class MotgamaWizardPago(models.TransientModel):
    _name = 'motgama.wizardpago'
    _description = 'Wizard Pagos'

    mediopago = fields.Many2one(string='Medio de Pago',comodel_name='motgama.mediopago',required=True)
    valor =  fields.Float(string=u'Valor a pagar',required=True)
    descripcion = fields.Char(string=u'Descripcion')

        
