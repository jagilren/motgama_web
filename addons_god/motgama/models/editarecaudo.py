from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaRecaudo(models.Model):
    _inherit = 'motgama.recaudo'

    anula_id = fields.Many2one(string="Recaudo de anulación",comodel_name="motgama.recaudo")

    @api.multi
    def anular(self):
        self.ensure_one()

        valoresPagos = []
        for pago in self.pagos:
            payment = False
            if pago.pago_id:
                move_lines = self.env['account.move.line'].search([('payment_id','=',pago.pago_id.id)])
                move_lines.sudo().remove_move_reconcile()
                valoresPayment = {
                    'amount': pago.pago_id.amount,
                    'currency_id': pago.pago_id.currency_id.id,
                    'journal_id': pago.pago_id.journal_id.id,
                    'payment_date': fields.Datetime().now(),
                    'payment_type': 'outbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'partner_id': pago.pago_id.partner_id.id
                }
                payment = self.env['account.payment'].sudo().create(valoresPayment)
                if not payment:
                    raise Warning('No fue posible cancelar el registro del pago')
                payment.sudo().post()
            valoresPago = {
                'movimiento_id': self.movimiento_id.id if self.movimiento_id else False,
                'cliente_id': self.cliente.id,
                'fecha': fields.Datetime().now(),
                'mediopago': pago.mediopago.id,
                'valor': 0 - pago.valor,
                'usuario_uid': self.env.user.id,
                'pago_id': payment.id if payment else False
            }
            valoresPagos.append(valoresPago)

        valoresRecaudo = {
            'movimiento_id': self.movimiento_id.id if self.movimiento_id else False,
            'habitacion': self.habitacion.id if self.habitacion else False,
            'cliente': self.cliente.id,
            'factura': self.factura.id,
            'total_pagado': 0 - self.total_pagado,
            'valor_pagado': 0 - self.valor_pagado,
            'tipo_recaudo': 'habitaciones' if self.habitacion else 'otros',
            'recepcion_id': self.recepcion_id.id,
            'pagos': [(0,0,valores) for valores in valoresPagos],
            'estado': 'anulado'
        }
        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('No fue posible anular el recaudo')

        self.sudo().write({'estado': 'anulado'})
    
    @api.multi
    def editar(self):
        self.ensure_one()

        if self.factura and self.factura.state in ['cancel','draft']:
            raise Warning('El estado de la factura ' + self.factura.number + ' no permite modificar el recaudo')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.editarecaudo',
            'name': 'Modificar recaudo',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

class MotgamaWizardEditaRecaudo(models.TransientModel):
    _name = 'motgama.wizard.editarecaudo'
    _description = 'Wizard Edita Recaudo'

    recaudo_ant_id = fields.Many2one(string="Recaudo anterior",comodel_name="motgama.recaudo",default=lambda self: self._get_recaudo())
    cliente_id = fields.Many2one(string='Cliente',comodel_name='res.partner',default=lambda self: self._get_cliente())
    total_a_pagar = fields.Float(string='Valor a pagar',default=lambda self: self._get_total())
    pago_ids = fields.Many2many(string='Pagos',comodel_name='motgama.wizard.editapago',default=lambda self: self._get_pagos())
    prenda_id = fields.Many2one(string='Prenda asociada',comodel_name='motgama.prendas',default=lambda self: self._get_prenda())
    valor_restante = fields.Float(string='Saldo restante',compute='_compute_restante')

    # Nueva Prenda
    pago_prenda = fields.Boolean(string='Pago con prenda',default=False,compute='_compute_prenda')
    prendas_pendientes = fields.Many2many(string='Prendas pendientes por pagar',comodel_name='motgama.prendas',compute='_compute_prendas')
    prendas_pagadas = fields.Many2many(string='Prendas pagadas',comodel_name='motgama.prendas',compute='_compute_prendas')

    prenda_descripcion = fields.Char(string='Descripción de la prenda')
    prenda_valor = fields.Float(string='Valor estimado de la prenda')

    @api.model
    def _get_recaudo(self):
        return self.env.context['active_id']

    @api.model
    def _get_cliente(self):
        rec = self.env['motgama.recaudo'].browse(self.env.context['active_id'])
        return rec.cliente.id

    @api.model
    def _get_total(self):
        rec = self.env['motgama.recaudo'].browse(self.env.context['active_id'])
        return rec.total_pagado
    
    @api.model
    def _get_pagos(self):
        rec = self.env['motgama.recaudo'].browse(self.env.context['active_id'])
        valoresPagos = []
        for pago in rec.pagos:
            valores = {
                'mediopago_id': pago.mediopago.id,
                'valor': pago.valor,
                'original': pago.mediopago.tipo == 'prenda'
            }
            valoresPagos.append(valores)
        return [(0,0,valores) for valores in valoresPagos]
    
    @api.model
    def _get_prenda(self):
        rec = self.env['motgama.recaudo'].browse(self.env.context['active_id'])
        return rec.prenda.id

    @api.depends('total_a_pagar','pago_ids.valor')
    def _compute_restante(self):
        for record in self:
            if record.total_a_pagar:
                restante = record.total_a_pagar
                for pago in record.pago_ids:
                    restante -= pago.valor
                record.valor_restante = restante
    
    @api.depends('pago_ids.valor')
    def _compute_prenda(self):
        for record in self:
            for pago in record.pago_ids:
                if pago.mediopago_id.tipo == 'prenda' and not pago.original:
                    record.pago_prenda = True

    @api.depends('cliente_id')
    def _compute_prendas(self):
        for recaudo in self:
            pagadas = []
            pendientes = []
            if recaudo.cliente_id:
                prendas = self.env['motgama.prendas'].search([('cliente_id','=',recaudo.cliente_id.id),'|',('active','=',True),('active','=',False)])
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

        valorPrenda = 0.0
        prenda = 0.0
        abonos = 0.0
        for pago in self.recaudo_ant_id.pagos:
            if pago.mediopago.tipo == 'prenda':
                prenda = pago.valor
                valorPrenda = pago.valor
            elif pago.mediopago.tipo == 'abono':
                abonos += pago.valor
        if prenda > 0 or abonos > 0:
            prenda_new = 0.0
            abonos_new = 0.0
            for pago in self.pago_ids:
                if pago.mediopago_id.tipo == 'prenda' and pago.original:
                    prenda_new += pago.valor
                elif pago.mediopago_id.tipo == 'abono':
                    abonos_new += pago.valor
            if abonos != abonos_new or prenda_new != prenda:
                raise Warning('Los pagos de prenda y abonos no pueden ser modificados, la modificación deberá realizarse directamente en el recaudo de cada abono o de la prenda, según sea el caso')
        
        if self.valor_restante >= 0.01:
            raise Warning('La cuenta no ha sido saldada')
        elif self.valor_restante < 0:
            raise Warning('El valor pagado es mayor al valor de la cuenta')

        valoresPagos = []
        cuenta_prenda = 0
        for pago in self.pago_ids:
            if pago.mediopago_id.tipo not in ['prenda','abono']:
                valoresPayment = {
                    'amount': pago.valor,
                    'currency_id': pago.mediopago_id.diario_id.company_id.currency_id.id,
                    'invoice_ids': [(4,self.recaudo_ant_id.factura.id)],
                    'journal_id': pago.mediopago_id.diario_id.id,
                    'payment_date': fields.Datetime().now(),
                    'payment_type': 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'partner_id': self.cliente_id.id
                }
                payment = self.env['account.payment'].sudo().create(valoresPayment)
                if not payment:
                    raise Warning('No fue posible crear el registro del pago')
                payment.post()
            elif pago.mediopago_id.tipo == 'prenda' and not pago.original:
                cuenta_prenda += 1
                if cuenta_prenda > 1:
                    raise Warning('No puede agregar más de una prenda nueva, si son varios artículos agréguelos como una sola prenda por el valor total de la deuda')
                valorPrenda += pago.valor
                valoresPrenda = {
                    'habitacion_id': self.recaudo_ant_id.habitacion.id if self.recaudo_ant_id.habitacion else False,
                    'movimiento_id': self.recaudo_ant_id.movimiento_id.id if self.recaudo_ant_id.movimiento_id else False,
                    'factura': self.recaudo_ant_id.factura.id if self.recaudo_ant_id.factura else False,
                    'tipovehiculo': self.recaudo_ant_id.movimiento_id.tipovehiculo if self.recaudo_ant_id.movimiento_id else False,
                    'placa': self.recaudo_ant_id.movimiento_id.placa_vehiculo if self.recaudo_ant_id.movimiento_id else False,
                    'cliente_id': self.cliente_id.id,
                    'descripcion': self.prenda_descripcion,
                    'valorprenda': self.prenda_valor,
                    'valordeuda': pago.valor,
                    'nroprenda': 'Nuevo'
                }
                self.env['motgama.prendas'].create(valoresPrenda)
            valores = {
                'movimiento_id': self.recaudo_ant_id.movimiento_id.id if self.recaudo_ant_id.movimiento_id else False,
                'cliente_id': self.cliente_id.id,
                'fecha': fields.Datetime().now(),
                'mediopago': pago.mediopago_id.id,
                'valor': pago.valor,
                'usuario_uid': self.env.user.id,
                'pago_id': payment.id if pago.mediopago_id.tipo not in ['prenda','abono'] else False
            }
            valoresPagos.append(valores)
        valoresRecaudo = {
            'movimiento_id': self.recaudo_ant_id.movimiento_id.id if self.recaudo_ant_id.movimiento_id else False,
            'habitacion': self.recaudo_ant_id.habitacion.id if self.recaudo_ant_id.habitacion else False,
            'cliente': self.cliente_id.id,
            'factura': self.recaudo_ant_id.factura.id,
            'total_pagado': self.total_a_pagar,
            'valor_pagado': self.total_a_pagar - valorPrenda,
            'tipo_recaudo': 'habitaciones' if self.recaudo_ant_id.habitacion else 'otros',
            'recepcion_id': self.recaudo_ant_id.recepcion_id.id,
            'pagos': [(0,0,valores) for valores in valoresPagos]
        }
        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('Error al crear el nuevo recaudo')
        nuevoRecaudo.factura.sudo().write({'recaudo':nuevoRecaudo.id})

        self.recaudo_ant_id.sudo().write({'modificado':True})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.recaudo',
            'name': nuevoRecaudo.nrorecaudo,
            'res_id': nuevoRecaudo.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current'
        }

class MotgamaWizardEditaPago(models.TransientModel):
    _name = 'motgama.wizard.editapago'
    _description = 'Wizard Edita Pago'

    mediopago_id = fields.Many2one(string='Medio de pago',comodel_name="motgama.mediopago")
    valor = fields.Float(string="Valor",required=True)
    pago_readonly = fields.Boolean(string="Solo lectura",default=False,compute="_compute_readonly")
    original = fields.Boolean(string="Original")

    @api.depends('mediopago_id')
    def _compute_readonly(self):
        for record in self:
            if record.mediopago_id and (record.mediopago_id.tipo == 'abono' or record.original):
                record.pago_readonly = True
            else:
                record.pago_readonly = False

    @api.multi
    def unlink(self):
        for record in self:
            if record.original or record.mediopago_id.tipo == 'abono':
                raise Warning('No debe modificar la prenda o los abonos de este recaudo')