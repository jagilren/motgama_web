from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime

class MotgamaWizardDesasigna(models.TransientModel):
    _inherit = 'motgama.wizarddesasigna'

    @api.multi
    def button_desasigna(self):
        self.ensure_one()
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        movimiento = flujo.ultmovimiento

        fechaActual = datetime.now()  # valida tiempo ocupada para validar parametro para autorizar         #P7.0.4R
        fecha_asigna = movimiento.asignafecha
        tiempo = fechaActual - fecha_asigna
        tiempoMinutos = tiempo.total_seconds() / 60
        flagDesasigna = self.env['motgama.parametros'].search([('codigo','=','TIEMPODESASIG')], limit=1)
        tiempoDesasigna = int(flagDesasigna.valor)
        if not tiempoDesasigna:
            raise Warning('Error en parámetro de Tiempo para Desasignar')

        if tiempoMinutos > tiempoDesasigna:
            raise Warning('Ya supero tiempo permitido para desasignar. '+str(int(tiempoMinutos)))  

        consumos = self.env['motgama.consumo'].search([('movimiento_id','=',movimiento.id)], limit=1)
        if consumos:  # si tiene consumos no se puede desasignar
            raise Warning('La habitación tiene consumos registrados, no se desasigna')   

        if movimiento:      # modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion      #P7.0.4R
            valores = {'desasignafecha':fechaActual,
                        'desasigna_uid':self.env.user.id,
                        'observacion':self.observacion}
            movimiento.write(valores)
            flujo.sudo().write({'estado':'RC'}) # pone en estado de aseo
            # TODO: Enviar correo de movimiento
        else:
            raise Warning('No se pudo cambiar el estado para desasignar la habitación')

        self.refresh_views()
        
        return True