from odoo import models, fields, api

class MotgamaPagos(models.Model):
    _name = 'motgama.pago'
    _description = 'Pago'
    movimiento_id = fields.Integer('Nro. Movimiento')
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente',required=True)   
    fecha = fields.Datetime(string='Fecha',default=lambda self: fields.Datetime().now())   
    mediopago = fields.Many2one(string='Medio de Pago',comodel_name='motgama.mediopago',required=True)
    valor =  fields.Float(string='Valor a pagar',required=True)
    # Se debe hacer la condicional que si el usuario va a pagar con prenda entonces se debe agregar el contacto que nos aparece desde odoo    
    descripcion = fields.Text(string='Descripcion')
    usuario_uid = fields.Integer(string='responsable',default=lambda self: self.env.user.id)
    recaudo = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo',ondelete='restrict')
    pago_id = fields.Many2one(string='Pago',comodel_name='account.payment')

class MotgamaRecaudo(models.Model):
    _name = 'motgama.recaudo'
    _description = 'Recaudo de hospedaje'
    _rec_name = 'nrorecaudo'

    nrorecaudo = fields.Char(string='Recaudo nro.',required=True,default='Nuevo')
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    recepcion_id = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')
    cliente = fields.Many2one(string='Cliente',comodel_name='res.partner')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    total_pagado = fields.Float(string='Valor total')
    pagos = fields.One2many(string='Pagos',comodel_name='motgama.pago',inverse_name='recaudo')
    prenda = fields.Many2one(string='Prenda asociada',comodel_name='motgama.prendas')
    valor_pagado = fields.Float(string='Valor pagado',default=0.0)
    usuario_uid = fields.Many2one(string='Usuario que recauda',comodel_name='res.users', default=lambda self: self.env.user.id)
    tipo_recaudo = fields.Selection(string='Tipo de recaudo',selection=[('habitaciones','Recaudo de habitaciones'),('abonos','Recaudo de abonos'),('prenda','Recaudo de prenda'),('anticipos','Recaudo de anticipos'),('otros','Otros recaudos')])
    estado = fields.Selection(string='Estado',selection=[('pagado','Pagado'),('anulado','Anulado')],default='pagado')
    modificado = fields.Boolean(string="Modificado",default=False)
    active = fields.Boolean(string='Activo',default=True)
    anula_id = fields.Many2one(string="Recaudo de anulación",comodel_name="motgama.recaudo")
    move_id = fields.Many2one(string="Asiento contable",comodel_name="account.move")

    @api.model
    def create(self,values):
        if values.get('nrorecaudo','Nuevo') == 'Nuevo':
            values['nrorecaudo'] = self.env['ir.sequence'].next_by_code('motgama.recaudo') or 'Nuevo'
        return super().create(values)

    @api.multi
    def anular(self, **kwargs):
        self.ensure_one()

        mediopago_id = self.env.ref('motgama.mediopago_abono').id
        abonos = self.pagos.filtered(lambda r: r.mediopago.id == mediopago_id)
        if 'force' in kwargs and kwargs['force']:
            force = True
        else:
            force = False
        if abonos and not force:
            return {
                'name': 'Anular recaudo con abonos',
                'type': 'ir.actions.act_window',
                'res_model': 'motgama.wizard_anula_recaudo',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new'
            }

        valoresPagos = []

        move_lines_reconcile = []
        for pago in self.pagos:
            payment = False
            if pago.pago_id:
                move_lines = self.env['account.move.line'].search([('payment_id','=',pago.pago_id.id)]).filtered(lambda r: r.account_id.reconcile)
                if self.tipo_recaudo in ['abonos','anticipos'] and self.move_id:
                    move_lines += self.move_id.line_ids.filtered(lambda r: r.account_id.reconcile)
                    recaudos = self.movimiento_id.recaudo_ids.filtered(lambda r: r.move_id.id == self.move_id.id and r.id != self.id)
                    for recaudo in recaudos:
                        pagos = recaudo.pagos.filtered(lambda r: r.pago_id)
                        for pago_id in pagos:
                            move_lines += self.env['account.move.line'].search([('payment_id','=',pago_id.id)]).filtered(lambda r: r.account_id.reconcile)
                move_lines.sudo().remove_move_reconcile()
                valoresPayment = {
                    'amount': pago.pago_id.amount,
                    'currency_id': pago.pago_id.currency_id.id,
                    'journal_id': pago.pago_id.journal_id.id,
                    'payment_date': fields.Datetime().now(),
                    'payment_type': 'outbound' if pago.pago_id.payment_type == 'inbound' else 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'partner_id': pago.pago_id.partner_id.id
                }
                paramAnticipos = self.env['motgama.parametros'].search([('codigo','=','CTAANTICIPO')],limit=1)
                if paramAnticipos and self.tipo_recaudo in ['abonos','anticipos']:
                    ant = self.cliente.property_account_receivable_id
                    cuenta = self.env['account.account'].sudo().search([('code','=',paramAnticipos.valor)],limit=1)
                    if not cuenta:
                        raise Warning('Se ha definido el parámetro: "CTAANTICIPO" como ' + paramAnticipos.valor + ', pero no existe una cuenta con ese código')
                    self.cliente.write({'property_account_receivable_id': cuenta.id})
                payment = self.env['account.payment'].sudo().create(valoresPayment)
                if not payment:
                    raise Warning('No fue posible cancelar el registro del pago')
                payment.sudo().post()
                if paramAnticipos and self.tipo_recaudo in ['abonos','anticipos']:
                    self.cliente.write({'property_account_receivable_id':ant.id})
                move_lines_reconcile.extend(self.env['account.move.line'].search([('payment_id','=',pago.pago_id.id)]).filtered(lambda r: r.account_id.reconcile).ids)
                move_lines_reconcile.extend(self.env['account.move.line'].search([('payment_id','=',payment.id)]).filtered(lambda r: r.account_id.reconcile).ids)
        
        if self.tipo_recaudo in ['abonos','anticipos'] and self.move_id:
            self.move_id.sudo().button_cancel()
            restar = self.valor_pagado
            zero = False
            tups = []
            for line in self.move_id.line_ids:
                abonado_ant = line.debit if line.debit > line.credit else line.credit
                abonado_new = abonado_ant - restar
                if abonado_new <= 0:
                    zero = True
                    continue
                tups.append((1,line.id,{
                    'debit': abonado_new if line.debit > line.credit else 0,
                    'credit': abonado_new if line.credit > line.debit else 0
                }))
            self.move_id.sudo().write({'line_ids':tups})
            if not zero:
                self.move_id.post()
                recaudos = self.movimiento_id.recaudo_ids.filtered(lambda r: r.move_id.id == self.move_id.id and r.id != self.id)
                for recaudo in recaudos:
                    pagos = recaudo.pagos.filtered(lambda r: r.pago_id)
                    for pago in pagos:
                        move_lines = self.env['account.move.line'].search([('payment_id','=',pago.id)]).filtered(lambda r: r.account_id.reconcile)
                        move_lines_reconcile.extend(move_lines.ids)
                move_lines_reconcile.extend(self.move_id.line_ids.filtered(lambda r: r.account_id.reconcile).ids)
                move_lines_reconcile.extend(self.factura.move_id.line_ids.filtered(lambda r: r.account_id.reconcile).ids)
            else:
                self.move_id.unlink()

        account_ids = []
        move_lines_reconcile = self.env['account.move.line'].browse(move_lines_reconcile)
        for line in move_lines_reconcile:
            if line.account_id.id in account_ids:
                continue
            account_ids.append(line.account_id.id)
        for account_id in account_ids:
            lines = move_lines_reconcile.filtered(lambda r: r.account_id.id == account_id)
            lines.reconcile()
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
            'estado': 'anulado',
            'active': False
        }
        nuevoRecaudo = self.env['motgama.recaudo'].create(valoresRecaudo)
        if not nuevoRecaudo:
            raise Warning('No fue posible anular el recaudo')

        self.sudo().write({'estado': 'anulado','active': False})
    
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

class MotgamaMedioPago(models.Model):
    _name = 'motgama.mediopago'
    _description = 'Medios de Pago'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre',required=True)
    tipo = fields.Selection(string='Tipo de pago',required=True,selection=[('electro','Electrónico'),('efectivo','Efectivo'),('pase','Pase/Cortesía'),('prenda','Prenda'),('abono','Abono')])
    lleva_prenda = fields.Boolean(string='¿Lleva Prenda?',compute='_compute_prenda')
    diario_id = fields.Many2one(string='Diario de pago',comodel_name='account.journal')
    active = fields.Boolean(string='Activo',default=True)
    cod = fields.Char(string="Código",size=2)

    @api.onchange('nombre')
    def onchange_nombre(self):
        if self.nombre:
            self.cod = self.nombre[:2].upper()

    @api.depends('tipo')
    def _compute_prenda(self):
        for record in self:
            record.lleva_prenda = record.tipo == 'prenda'