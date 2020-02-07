from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_precuenta(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardprecuenta',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.form_wizard_precuenta').id,
            'target': 'new',
            'name': 'Precuenta de la habitación ' + self.codigo
        }

class MotgamaWizardPrecuenta(models.TransientModel):
    _name = 'motgama.wizardprecuenta'
    _description = 'Visualización de Precuenta'

    fecha_asignacion = fields.Datetime(string='Fecha de Asignación', default=lambda self: self._get_fecha())
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    movimiento_id = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',compute="_compute_movimiento")
    consumos = fields.Many2many(string='Consumos',comodel_name='motgama.consumo',default=lambda self: self._get_consumos())
    incluye_ocasional = fields.Boolean(default=False,compute='_compute_precio')
    incluye_amanecida = fields.Boolean(default=False,compute='_compute_precio')
    incluye_adicional = fields.Boolean(default=False,compute='_compute_precio')
    hospedaje_normal = fields.Float(string='Hospedaje Ocasional',compute='_compute_precio')
    hospedaje_amanecida = fields.Float(string='Hospedaje Amanecida',compute='_compute_precio')
    hospedaje_adicional = fields.Float(string='Hospedaje Adicional',compute='_compute_precio')
    valor_total = fields.Float(string='Total hospedaje',compute='_compute_total')
    abono_ids = fields.Many2many(string="Abonos",comodel_name='motgama.recaudo',compute="_compute_abonos")
    adeudado = fields.Float(string='Total a pagar',compute="_compute_adeudado")
    abonado = fields.Float(string="Total abonado",compute="_compute_abonado")
    movimiento = fields.Boolean()

    @api.model
    def _get_fecha(self):
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)],limit=1)
        return flujo.ultmovimiento.asignafecha

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.depends('habitacion')
    def _compute_movimiento(self):
        for record in self:
            if record.habitacion:
                record.movimiento_id = record.habitacion.ultmovimiento

    @api.model
    def _get_consumos(self):
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        return flujo.consumos

    @api.depends('habitacion','movimiento')
    def _compute_precio(self):
        for record in self:
            if record.habitacion and record.movimiento_id:
                precioAmanecida = 0
                precioOcasional = 0
                precioAdicional = 0
                fechaActual = fields.Datetime().now()

                if record.habitacion.estado == 'OA':
                    precioAmanecida = record.movimiento_id.tarifamanecida
                    record.incluye_amanecida = True
                    record.incluye_ocasional = False
                    if fechaActual < record.movimiento_id.horainicioamanecida:
                        raise Warning('Esta asignación no ha superado la "Hora Inicio Amanecida" definida en el Calendario, debe cambiar el plan de asignación a "Ocupada Ocasional" para liquidar esta habitación en este momento')
                    elif record.movimiento_id.asignafecha < record.movimiento_id.horainicioamanecida:
                        delta = record.movimiento_id.horainicioamanecida - record.movimiento_id.asignafecha
                        segundos = delta.total_seconds()
                        horas = segundos // 3600
                        minutos = (segundos // 60) % 60
                        tiempoGraciaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOGRACIA')])
                        if not tiempoGraciaStr:
                            raise Warning('No existe el parámetro "TIEMPOGRACIA"')
                        try:
                            tiempoGracia = int(tiempoGraciaStr.valor)
                        except ValueError:
                            raise Warning('El parámetro "TIEMPOGRACIA" está mal definido, contacte al administrador')
                        seCobraFraccionStr = self.env['motgama.parametros'].search([('codigo','=','COBRAFRACHORA')])
                        if not seCobraFraccionStr:
                            raise Warning('No existe el parámetro "COBRAFRACHORA"')
                        if seCobraFraccionStr.valor == 'S':
                            seCobraFraccion = True
                        elif seCobraFraccionStr.valor == 'N':
                            seCobraFraccion = False
                        else:
                            raise Warning('El parámetro "COBRAFRACHORA" está mal definido, contacte al administrador')
                        if minutos > tiempoGracia:
                            if seCobraFraccion:
                                horas = float(horas) + float(minutos) / 60.0
                            else:
                                horas += 1
                        horasAntes = horas
                    else:
                        horasAntes = 0
                    
                    if fechaActual > record.movimiento_id.horafinamanecida:
                        delta = fechaActual - record.movimiento_id.horafinamanecida
                        segundos = delta.total_seconds()
                        horas = segundos // 3600
                        minutos = (segundos // 60) % 60
                        tiempoGraciaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOGRACIA')])
                        if not tiempoGraciaStr:
                            raise Warning('No existe el parámetro "TIEMPOGRACIA"')
                        try:
                            tiempoGracia = int(tiempoGraciaStr.valor)
                        except ValueError:
                            raise Warning('El parámetro "TIEMPOGRACIA" está mal definido, contacte al administrador')
                        seCobraFraccionStr = self.env['motgama.parametros'].search([('codigo','=','COBRAFRACHORA')])
                        if not seCobraFraccionStr:
                            raise Warning('No existe el parámetro "COBRAFRACHORA"')
                        if seCobraFraccionStr.valor == 'S':
                            seCobraFraccion = True
                        elif seCobraFraccionStr.valor == 'N':
                            seCobraFraccion = False
                        else:
                            raise Warning('El parámetro "COBRAFRACHORA" está mal definido, contacte al administrador')
                        if minutos > tiempoGracia:
                            if seCobraFraccion:
                                horas = float(horas) + float(minutos) / 60.0
                            else:
                                horas += 1
                        horasDespues = horas
                    else:
                        horasDespues = 0
                    
                    horasAdicionales = horasAntes + horasDespues

                elif record.habitacion.estado == 'OO':
                    record.incluye_ocasional = True
                    record.incluye_amanecida = False
                    precioOcasional = record.movimiento_id.tarifaocasional
                    tiempoOcasionalStr = record.movimiento_id.tiemponormalocasional
                    try:
                        tiempoOcasional = int(tiempoOcasionalStr)
                    except ValueError:
                        raise Warning('El parámetro de tiempo normal ocasional en el calendario está mal definido, contacte al administrador')
                    delta = fechaActual - record.movimiento_id.asignafecha
                    segundos = delta.total_seconds()
                    segundosOcasional = tiempoOcasional * 3600
                    if segundos > segundosOcasional:
                        segundos -= segundosOcasional
                        horas = segundos // 3600
                        minutos = (segundos // 60) % 60
                        tiempoGraciaStr = self.env['motgama.parametros'].search([('codigo','=','TIEMPOGRACIA')])
                        if not tiempoGraciaStr:
                            raise Warning('No existe el parámetro "TIEMPOGRACIA"')
                        try:
                            tiempoGracia = int(tiempoGraciaStr.valor)
                        except ValueError:
                            raise Warning('El parámetro "TIEMPOGRACIA" está mal definido, contacte al administrador')
                        seCobraFraccionStr = self.env['motgama.parametros'].search([('codigo','=','COBRAFRACHORA')])
                        if not seCobraFraccionStr:
                            raise Warning('No existe el parámetro "COBRAFRACHORA"')
                        if seCobraFraccionStr.valor == 'S':
                            seCobraFraccion = True
                        elif seCobraFraccionStr.valor == 'N':
                            seCobraFraccion = False
                        else:
                            raise Warning('El parámetro "COBRAFRACHORA" está mal definido, contacte al administrador')
                        if minutos > tiempoGracia:
                            if seCobraFraccion:
                                horas = float(horas) + float(minutos) / 60.0
                            else:
                                horas += 1
                        horasAdicionales = horas
                    else:
                        horasAdicionales = 0
                
                precioAdicional = record.movimiento_id.tarifahoradicional * horasAdicionales
                if precioAdicional > 0:
                    record.incluye_adicional = True
                else:
                    record.incluye_adicional = False

                record.hospedaje_normal = precioOcasional
                record.hospedaje_amanecida = precioAmanecida
                record.hospedaje_adicional = precioAdicional
    
    @api.depends('consumos','hospedaje_normal','hospedaje_amanecida','hospedaje_adicional')
    def _compute_total(self):
        for record in self:
            precio = record.hospedaje_normal + record.hospedaje_amanecida + record.hospedaje_adicional
            for consumo in record.consumos:
                precio += consumo.vlrSubtotal
            record.valor_total = precio

    @api.depends('movimiento_id')
    def _compute_abonos(self):
        for record in self:
            if record.movimiento_id:
                ids = [recaudo.id for recaudo in record.movimiento_id.recaudo_ids]
                record.abono_ids = [(6,0,ids)]
    
    @api.depends('abono_ids.valor_pagado')
    def _compute_abonado(self):
        for record in self:
            abonado = 0.0
            for abono in record.abono_ids:
                abonado += abono.valor_pagado
            record.abonado = abonado
    
    @api.depends('valor_total','abonado')
    def _compute_adeudado(self):
        for record in self:
            record.adeudado = record.valor_total - record.abonado