from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime, timedelta
import pytz

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    es_hospedaje = fields.Boolean(default=False)
    asignafecha = fields.Datetime(string="Ingreso",compute="_compute_asignafecha",store=True)
    liquidafecha = fields.Datetime(string="Salida")

    @api.depends('movimiento')
    def _compute_asignafecha(self):
        for record in self:
            if record.movimiento:
                record.asignafecha = record.movimiento.asignafecha

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_liquidar(self):
        self.ensure_one()
        if not self.env.user.motgama_liquida_habitacion:
            raise Warning('No tiene permitido liquidar habitaciones, contacte al administrador')
        movimiento = self.ultmovimiento
        fechaActual = fields.Datetime().now()

        if not self.env.user.tz:
            tz = pytz.timezone('America/Bogota')
        else:
            tz = pytz.timezone(self.env.user.tz)

        if not self.puede_liquidar:
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
                self.write({'puede_liquidar': True})
        
        # Se calculan las horas adicionales si es amanecida
        if self.estado == 'OA':
            if fechaActual < movimiento.horainicioamanecida:
                raise Warning('Esta asignación no ha superado la "Hora Inicio Amanecida" definida en el Calendario, debe cambiar el plan de asignación a "Ocupada Ocasional" para liquidar esta habitación en este momento')
            elif movimiento.asignafecha < movimiento.horainicioamanecida:
                delta = movimiento.horainicioamanecida - movimiento.asignafecha
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
            
            if fechaActual > movimiento.horafinamanecida:
                delta = fechaActual - movimiento.horafinamanecida
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

            ordenVenta = self.env['sale.order'].search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
            if not ordenVenta:
                cliente = self.env['res.partner'].search([('vat','=','1')], limit=1)
                if not cliente:
                    raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')
                valores = {
                    'partner_id' : cliente.id,
                    'movimiento' : movimiento.id
                }
                ordenVenta = self.env['sale.order'].create(valores)
                if not ordenVenta:
                    raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
                ordenVenta.action_confirm()

            codAmanecida = self.env['motgama.parametros'].search([('codigo','=','CODHOSAMANE')])
            if not codAmanecida:
                raise Warning('No existe el parámetro "CODHOSAMANE"')
            producto = self.env['product.template'].search([('default_code','=',codAmanecida.valor)])
            if not producto:
                raise Warning('No existe producto con Referencia interna: ' + codAmanecida.valor + ' para Hospedaje Amanecida')
            valoresLineaAmanecida = {
                'customer_lead' : 0,
                'name' : producto.name,
                'order_id' : ordenVenta.id,
                'price_unit' : movimiento.tarifamanecida,
                'product_uom_qty' : 1,
                'product_id' : producto.product_variant_id.id,
                'es_hospedaje' : True
            }
            nuevaLinea = self.env['sale.order.line'].create(valoresLineaAmanecida)
            if not nuevaLinea:
                raise Warning('Error al liquidar: No se pudo agregar el hospedaje de amanecida a la orden de venta')

        elif self.estado == 'OO':
            tiempoOcasionalStr = movimiento.tiemponormalocasional
            try:
                tiempoOcasional = int(tiempoOcasionalStr)
            except ValueError:
                raise Warning('El parámetro de tiempo normal ocasional en el calendario está mal definido, contacte al administrador')
            delta = fechaActual - movimiento.asignafecha
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
            
            ordenVenta = self.env['sale.order'].search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
            if not ordenVenta:
                cliente = self.env['res.partner'].search([('vat','=','1')], limit=1)
                if not cliente:
                    raise Warning('No se ha agregado el cliente genérico (NIT: 1), contacte al administrador')
                valores = {
                    'partner_id' : cliente.id,
                    'movimiento' : movimiento.id
                }
                ordenVenta = self.env['sale.order'].create(valores)
                if not ordenVenta:
                    raise Warning('Error al registrar el consumo: No se pudo crear orden de venta')
                ordenVenta.action_confirm()
            ordenVenta.write({'es_hospedaje':True})

            codOcasional = self.env['motgama.parametros'].search([('codigo','=','CODHOSOCASIO')])
            if not codOcasional:
                raise Warning('No existe el parámetro "CODHOSOCASIO"')
            producto = self.env['product.template'].search([('default_code','=',codOcasional.valor)])
            if not producto:
                raise Warning('No existe producto con Referencia interna: ' + codOcasional.valor + ' para Hospedaje Ocasional')
            valoresLineaOcasional = {
                'customer_lead' : 0,
                'name' : producto.name,
                'order_id' : ordenVenta.id,
                'price_unit' : movimiento.tarifaocasional,
                'product_uom_qty' : 1,
                'product_id' : producto.product_variant_id.id,
                'es_hospedaje' : True
            }
            nuevaLinea = self.env['sale.order.line'].create(valoresLineaOcasional)
            if not nuevaLinea:
                raise Warning('Error al liquidar: No se pudo agregar el hospedaje ocasional a la orden de venta')
        else:
            raise Warning('Error del sistema, la habitación no está ocupada')

        if horasAdicionales != 0:
            codAdicionales = self.env['motgama.parametros'].search([('codigo','=','CODHOSADCNAL')])
            if not codAdicionales:
                raise Warning('No existe el parámetro "CODHOSADCNAL"')
            producto = self.env['product.template'].search([('default_code','=',codAdicionales.valor)])
            if not producto:
                raise Warning('No existe producto con Referencia interna: ' + codAdicionales.valor + ' para Hospedaje Adicional')
            valoresLineaAdicionales = {
                'customer_lead' : 0,
                'name' : producto.name,
                'order_id' : ordenVenta.id,
                'price_unit' : round(movimiento.tarifahoradicional),
                'product_uom_qty' : horasAdicionales,
                'product_id' : producto.product_variant_id.id,
                'es_hospedaje' : True
            }
            nuevaLinea = self.env['sale.order.line'].create(valoresLineaAdicionales)
            if not nuevaLinea:
                raise Warning('Error al liquidar: No se pudo agregar el hospedaje de horas adicionales a la orden de venta')
        
        self.write({'estado':'LQ','orden_venta':ordenVenta.id,'notificar':True})
        movimiento.write({'liquidafecha':fechaActual,'liquida_uid':self.env.user.id,'ordenVenta':ordenVenta.id})
        ordenVenta.write({'liquidafecha':fechaActual})

        self.puede_liquidar = False

        return True

    @api.multi
    def button_cuentacobro(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.orden_venta.id,
            'target': 'current'
        }