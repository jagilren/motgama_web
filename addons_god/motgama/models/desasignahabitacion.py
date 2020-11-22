from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime, timedelta

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def desasigna(self):
        if not self.env.ref('motgama.motgama_desasigna') in self.env.user.permisos:
            raise Warning('No tiene permitido desasignar habitaciones, contacte al administrador')

        return {
            'type': 'ir.actions.act_window',
            'res_model': "motgama.wizarddesasigna",
            'name': "Desasigna habitacion",
            'view_type': "form",
            'view_mode': "form",
            'target': "new"
        }

class MotgamaWizardDesasigna(models.TransientModel):
    _inherit = 'motgama.wizarddesasigna'

    @api.multi
    def button_desasigna(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_desasigna') in self.env.user.permisos:
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
            raise Warning('Error en parámetro de Tiempo para Desasignar')

        if tiempoMinutos > tiempoDesasigna:
            raise Warning('Ya superó el tiempo permitido para desasignar. Van ' + str(int(tiempoMinutos)) + ' minutos')  

        consumos = self.env['motgama.consumo'].search([('movimiento_id','=',movimiento.id)], limit=1)
        if consumos:  # Si tiene consumos no se puede desasignar
            raise Warning('La habitación tiene consumos registrados, no se desasigna')   

        if movimiento:  # Modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion                #P7.0.4R
            valores = {'desasignafecha':fechaActual,
                        'desasigna_uid':self.env.user.id,
                        'observacion':self.observacion}
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