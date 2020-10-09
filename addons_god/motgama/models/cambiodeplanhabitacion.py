import time
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

class MotgamaCambioPlan(models.Model):
    _name = 'motgama.cambioplan'
    _description = 'Registro de cambio de plan de habitación'

    fecha = fields.Datetime(string='Fecha del cambio',default=lambda self: fields.Datetime().now())
    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',ondelete='set null')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    plan_anterior = fields.Selection(string='Plan anterior',selection=[('OO','Ocasional'),('OA','Amanecida')])
    plan_nuevo = fields.Selection(string='Plan nuevo',selection=[('OO','Ocasional'),('OA','Amanecida')])

class MotgamaWizardCambiodeplan(models.TransientModel):
    _inherit = 'motgama.wizardcambiodeplan'

    @api.multi
    def button_cambio_plan(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_cambio_plan') in self.env.user.permisos:
            raise Warning('No tiene permitido cambiar el hospedaje de una habitación, contacte al administrador')

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
            flagFinInicioAmanecida = calendario.horafininicioamanecida
            if not flagInicioAmanecida:
                raise Warning('No se ha definido "Hora inicio amanecida" en el calendario')
            if not flagfinAmanecida:
                raise Warning('No se ha definido "Hora fin amanecida" en el calendario')
            if not flagFinInicioAmanecida:
                raise Warning('No se ha definido "Hora fin amanecida" en el calendario')
            if flagInicioAmanecida == '0' and flagfinAmanecida == '0':
                raise Warning('No se admite amanecida')
            # CONDICION -> Horas en formato 24 horas HORAS:MINUTOS
            flagInicioTz = datetime.strptime(str(flagInicioAmanecida),"%H:%M")
            flagFinTz = datetime.strptime(str(flagfinAmanecida),"%H:%M")
            flagFinInicioTz = datetime.strptime(str(flagFinInicioAmanecida),"%H:%M")
            #flagInicio = tz.localize(flagInicioTz).astimezone(pytz.utc).time()
            #flagFin = tz.localize(flagFinTz).astimezone(pytz.utc).time()
            if flagInicioTz > flagFinInicioTz:
                if flagFinInicioTz.time() < fechaActualTz.time() < flagInicioTz.time():
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
                else:
                    # if not (flagInicio < fechaActual.time() < flagFin): # OJO No incluye los extremos
                    #     raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
                    flujo.sudo().write({'estado':'OA'}) # pone en estado de ocupada Amanecida
                    movimiento.write({'asignatipo':'OA','hubocambioplan':True,'observacion':self.observacion})
                    valores = {
                        'movimiento': movimiento.id,
                        'habitacion': flujo.id,
                        'plan_anterior': 'OO',
                        'plan_nuevo': 'OA'
                    }
            else:
                if not (flagInicioTz.time() <= fechaActualTz.time() <= flagFinInicioTz.time()): # OJO No incluye los extremos
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
                else:
                    flujo.sudo().write({'estado':'OA'}) # pone en estado de ocupada Amanecida
                    movimiento.write({'asignatipo':'OA','hubocambioplan':True,'observacion':self.observacion})
                    valores = {
                        'movimiento': movimiento.id,
                        'habitacion': flujo.id,
                        'plan_anterior': 'OO',
                        'plan_nuevo': 'OA'
                    }
            
            valoresNotifica = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.wizardcambiodeplan',
                'tipo_evento': 'registro',
                'asunto': 'La habitación ' + flujo.codigo + ' ha cambiado de plan a Amanecida',
                'descripcion': 'El usuario ' + self.env.user.name + ' ha cambiado el plan de la habitación ' + flujo.codigo + ' a Amanecida'
            }

        else:   # Va a pasar de amanecida a ocasional
            flujo.sudo().write({'estado':'OO'}) # pone en estado de ocupada ocasional
            movimiento.write({'asignatipo':'OO','hubocambioplan':True,'observacion':self.observacion})
            valores = {
                'movimiento': movimiento.id,
                'habitacion': flujo.id,
                'plan_anterior': 'OA',
                'plan_nuevo': 'OO'
            }

            valoresNotifica = {
                'fecha': fields.Datetime().now(),
                'modelo': 'motgama.wizardcambiodeplan',
                'tipo_evento': 'registro',
                'asunto': 'La habitación ' + flujo.codigo + ' ha cambiado de plan a Ocasional',
                'descripcion': 'El usuario ' + self.env.user.name + ' ha cambiado el plan de la habitación ' + flujo.codigo + ' a Ocasional'
            }

        nuevoRegistro = self.env['motgama.cambioplan'].create(valores)
        if not nuevoRegistro:
            raise Warning('No se pudo crear el registro del cambio de plan')

        self.env['motgama.log'].create(valoresNotifica)
        
        self.refresh_views()
        
        return True