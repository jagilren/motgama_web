import time
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

class MotgamaWizardCambiodeplan(models.TransientModel):
    _inherit = 'motgama.wizardcambiodeplan'

    @api.multi
    def button_cambio_plan(self):
        self.ensure_one()
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        habitacion = self.env['motgama.habitacion'].search([('codigo','=',flujo['codigo'])])
        movimiento = flujo.ultmovimiento
        fechaActual = datetime.now()

        if flujo.estado == 'OO': # para pasar de ocasional a amanecida debe validar la hora             #P7.0.4R
            if not self.env.user.tz:
                tz = pytz.timezone('America/Bogota')
            else:
                tz = pytz.timezone(self.env.user.tz)
            #if not tz:
            #    raise Warning('El usuario no tiene una zona horaria definida, contacte al administrador')

            # Esto me da el numero del dia de la semana, python arranca con 0->lunes                #P7.0.4R
            fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
            nroDia = fechaActualTz.weekday()
            calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
            if not calendario:
                raise Warning('Error: no existe calendario para el dia actual ',int(nroDia))
            flagInicioAmanecida = calendario.horainicioamanecida
            flagfinAmanecida = calendario.horafinamanecida
            if not flagInicioAmanecida:
                raise Warning('No se ha definido "Hora Inicio Amanecida" en el calendario')
            if not flagfinAmanecida:
                raise Warning('No se ha definido "Hora Fin Amanecida" en el calendario')
            if flagInicioAmanecida == '0' and flagfinAmanecida == '0':
                raise Warning('No se admite amanecida')
            # CONDICION -> Horas en formato 24 horas HORAS:MINUTOS
            flagInicioTz = datetime.strptime(str(flagInicioAmanecida),"%H:%M")
            flagFinTz = datetime.strptime(str(flagfinAmanecida),"%H:%M")
            #flagInicio = tz.localize(flagInicioTz).astimezone(pytz.utc).time()
            #flagFin = tz.localize(flagFinTz).astimezone(pytz.utc).time()
            if flagInicioTz > flagFinTz:
                if flagFinTz.time() < fechaActualTz.time() < flagInicioTz.time():
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
                else:
                    # if not (flagInicio < fechaActual.time() < flagFin): # OJO No incluye los extremos
                    #     raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
                    flujo.sudo().write({'estado':'OA'}) # pone en estado de ocupada Amanecida

        else:   # Va a pasar de amanecida a ocasional
            flujo.sudo().write({'estado':'OO'}) # pone en estado de ocupada ocasional
        
        self.refresh_views()
        
        return True

        


