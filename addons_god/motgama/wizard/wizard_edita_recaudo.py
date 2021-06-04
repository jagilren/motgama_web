from odoo import models, fields, api
from odoo.exceptions import Warning

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
        if abs(self.valor_restante) >= 0.01:
            raise Warning('La cuenta no ha sido saldada')
        elif self.valor_restante < 0:
            raise Warning('El valor pagado es mayor al valor de la cuenta')

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
        move_lines_reconcile = self.env['account.move.line']
        if self.recaudo_ant_id.tipo_recaudo in ['abonos','anticipos'] and self.recaudo_ant_id.move_id:
            move_lines_reconcile += self.recaudo_ant_id.move_id.line_ids.filtered(lambda r: r.account_id.reconcile)
            move_lines_reconcile.remove_move_reconcile()
            self.recaudo_ant_id.move_id.button_cancel()
            new_value = move_lines_reconcile[0].credit + self.total_a_pagar if move_lines_reconcile[0].credit > 0 else move_lines_reconcile[0].debit + self.total_a_pagar
            self.recaudo_ant_id.move_id.write({
                'line_ids': [(1,line.id,{
                    'debit': new_value if line.debit > 0 else 0,
                    'credit': new_value if line.credit > 0 else 0
                }) for line in self.recaudo_ant_id.move_id.line_ids]
            })
        for pago in self.pago_ids:
            if pago.mediopago_id.tipo not in ['prenda','abono']:
                valoresPayment = {
                    'amount': pago.valor,
                    'currency_id': pago.mediopago_id.diario_id.company_id.currency_id.id,
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
                move_lines_reconcile += self.env['account.move.line'].search([('payment_id','=',payment.id)]).filtered(lambda r: r.account_id.reconcile)
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
        for recaudo in self.recaudo_ant_id.movimiento_id.recaudo_ids:
            for pago in recaudo.pagos.filtered(lambda r: r.pago_id):
                move_lines = self.env['account.move.line'].search([('payment_id','=',pago.pago_id.id)]).filtered(lambda r: r.account_id.reconcile)
                move_lines.remove_move_reconcile()
                move_lines_reconcile += move_lines
        move_lines_reconcile += self.recaudo_ant_id.factura.move_id.line_ids.filtered(lambda r: r.account_id.reconcile)
        account_ids = []
        for line in move_lines_reconcile:
            if line.account_id.id in account_ids:
                continue
            account_ids.append(line.account_id.id)
        self.recaudo_ant_id.move_id.post()
        for account_id in account_ids:
            move_lines_reconcile.filtered(lambda r: r.account_id.id == account_id).reconcile()
        valoresRecaudo = {
            'movimiento_id': self.recaudo_ant_id.movimiento_id.id if self.recaudo_ant_id.movimiento_id else False,
            'habitacion': self.recaudo_ant_id.habitacion.id if self.recaudo_ant_id.habitacion else False,
            'cliente': self.cliente_id.id,
            'factura': self.recaudo_ant_id.factura.id,
            'total_pagado': self.total_a_pagar,
            'valor_pagado': self.total_a_pagar - valorPrenda,
            'tipo_recaudo': self.recaudo_ant_id.tipo_recaudo,
            'recepcion_id': self.recaudo_ant_id.recepcion_id.id,
            'pagos': [(0,0,valores) for valores in valoresPagos],
            'move_id': self.recaudo_ant_id.move_id.id if  self.recaudo_ant_id.move_id else False
        }
        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('Error al crear el nuevo recaudo')
        if self.recaudo_ant_id.tipo_recaudo not in ['anticipos','abonos']:
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

class MotgamaWizardAnulaRecaudo(models.TransientModel):
    _name = 'motgama.wizard_anula_recaudo'
    _description = 'Wizard Edita Recaudo'

    desc = {
        'recaudo': '''
            Si anula solo este recaudo, se van a anular todos los pagos registrados excepto los abonos y la prenda (si hay).
            Si desea anular también los abonos debe seleccionar "Este recaudo y todos los abonos" en Tipo de anulación.
            Para liberar la prenda es necesario ir manualmente a la prenda y darle de baja.

            ¿Está seguro que desea anular este recaudo?
        ''',
        'todo': '''
            Va a anular este recaudo con todos los pagos y abonos relacionados.
            Si existe prenda asociada y desea liberarla deberá ir manualmente a la prenda y darle de baja.

            ¿Está seguro que desea anular este recaudo?
        '''
    }

    tipo_anulacion = fields.Selection(string="Tipo de anulación",selection=[('recaudo','Solo este recaudo'),('todo','Este recaudo y todos los abonos')],default="recaudo")
    descripcion = fields.Text(string="Descripción",compute="_compute_descripcion")

    @api.depends('tipo_anulacion')
    def _compute_descripcion(self):
        for record in self:
            if record.tipo_anulacion:
                record.descripcion = self.desc[record.tipo_anulacion]

    def anular(self):
        self.ensure_one()

        id_recaudo = self.env.context['active_id']
        recaudo = self.env['motgama.recaudo'].browse(id_recaudo)
        if self.tipo_anulacion == 'recaudo':
            recaudo.anular(force=True)
        else:
            for abono in recaudo.movimiento_id.recaudo_ids:
                abono.anular(force=True)
        return True