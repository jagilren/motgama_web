from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime, timedelta

class MotgamaWizardDesasigna(models.TransientModel):
    _inherit = 'motgama.wizarddesasigna'

    @api.multi
    def button_desasigna(self):
        self.ensure_one()
        if not self.env.user.motgama_desasigna:
            raise Warning('No tiene permitido desasignar habitaciones, contacte al administrador')

        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        movimiento = flujo.ultmovimiento

        fechaActual = datetime.now()  # Valida tiempo ocupada para validar parametro para autorizar         #P7.0.4R
        fecha_asigna = movimiento.asignafecha
        tiempo = fechaActual - fecha_asigna
        tiempoMinutos = tiempo.total_seconds() / 60
        flagDesasigna = self.env['motgama.parametros'].search([('codigo','=','TIEMPODESASIG')],limit=1)
        if not flagDesasigna:
            raise Warning('El parámetro "TIEMPODESASIG" no se ha definido')
        tiempoDesasigna = int(flagDesasigna.valor)
        if not tiempoDesasigna:
            raise Warning('Error: Parámetro "TIEMPODESASIG" está mal definido')

        if tiempoMinutos > tiempoDesasigna:
            raise Warning('Ya superó el tiempo permitido para desasignar. Van ' + str(int(tiempoMinutos)) + ' minutos')  

        consumos = self.env['motgama.consumo'].search([('movimiento_id','=',movimiento.id)])
        puede_desasignar = True
        cantidad_productos = {}
        for consumo in consumos:
            if consumo.producto_id in cantidad_productos:
                cantidad_productos[consumo.producto_id] += consumo.cantidad
            else:
                cantidad_productos[consumo.producto_id] = consumo.cantidad
        for producto in cantidad_productos:
            if cantidad_productos[producto] > 0:
                puede_desasignar = False
        if not puede_desasignar:
            raise Warning('La habitación tiene consumos registrados, no se puede desasignar')   

        if movimiento:  # Modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion                #P7.0.4R
            orden_venta = self.env['sale.order'].search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
            if orden_venta:
                for picking in orden_venta.picking_ids:
                    picking.sudo().write({'sale_id': False})
                orden_venta.action_cancel()
                if not orden_venta.state == 'cancel':
                    raise Warning('No se pudo cancelar la orden de venta')
            valores = {
                'desasignafecha':fechaActual,
                'desasigna_uid':self.env.user.id,
                'observacion':self.observacion
            }
            movimiento.write(valores)
            flujo.sudo().write({'estado':'RC','notificar':True}) # pone en estado de aseo

            valores = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.wizarddesasigna',
                'tipo_evento': 'correo',
                'asunto': 'La habitación ' + flujo.codigo + ' ha sido desasignada',
                'descripcion': 'El usuario ' + self.env.user.name + ' ha desasignado la habitación ' + flujo.codigo + ', la cual fue asignada hace ' + str(round(tiempoMinutos)) + ' minutos. Observaciones: ' + self.observacion
            }
            self.env['motgama.log'].create(valores)
        else:
            raise Warning('No se pudo cambiar el estado para desasignar la habitación')

        self.refresh_views()
        
        return True