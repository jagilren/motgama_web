from odoo import models, fields, api
import pytz
from datetime import datetime, timedelta

class MotgamaWizardHabitacion(models.TransientModel):
    _name = 'motgama.wizardhabitacion'
    _description = 'Asignacion de habitacion'
    placa = fields.Char(string='Ingrese Placa',)
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')],default='peaton',required=True)
    asignatipo = fields.Selection(string='La Asignacion es Amanecida?',selection=[('OO', 'No'), ('OA', 'Si')],required=True,default='OO')
    
    valorocasional = fields.Float(string='Valor Hospedaje Ocasional',readonly=True,compute='_compute_valores')
    valoramanecida = fields.Float(string='Valor Hospedaje Amanecida',readonly=True,compute='_compute_valores')
    valoradicional = fields.Float(string='Valor Hora Adicional',readonly=True,compute='_compute_valores')
    horainicioamanecida = fields.Datetime(string='Hora Inicio Amanecida',readonly=True,compute='_compute_valores')
    tiemponormal = fields.Char(string='Tiempo normal ocasional',readonly=True)
    fecha = fields.Datetime(string='Fecha y hora del sistema',default=lambda self: fields.Datetime().now(),readonly=True)

    codigohab = fields.Char(compute='_compute_valores')

    observacion = fields.Text(string="¡Atención! la habitación tiene las siguientes observaciones",default=lambda self: self._get_observacion())

    @api.depends('tipovehiculo')
    def _compute_valores(self):
        for record in self:
            flujo_id = self.env.context['active_id']
            flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)], limit=1)
            Habitacion = flujo['codigo']
            fullHabitacion = self.env['motgama.habitacion'].search([('codigo','=',Habitacion)], limit=1) # Trae todos los datos de la habitacion actual
            fechaActual = datetime.now()
            if not self.env.user.tz:
                tz = pytz.timezone('America/Bogota')
            else:
                tz = pytz.timezone(self.env.user.tz)
            fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
            nroDia = fechaActualTz.weekday()
            calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
            if not calendario:
                raise Warning('Error: No existe calendario para el día actual')
            
            record.codigohab = Habitacion

            horaInicioAmanecida = datetime.strptime(str(calendario.horainicioamanecida),"%H:%M") + timedelta(hours=5)
            fechaInicioAmanecida = datetime(year=fechaActualTz.year,month=fechaActualTz.month,day=fechaActualTz.day,hour=horaInicioAmanecida.hour,minute=horaInicioAmanecida.minute)
            record.horainicioamanecida = fechaInicioAmanecida
            record.tiemponormal = str(calendario.tiemponormalocasional) + ' horas'

            flagInicioDia = self.env['motgama.parametros'].search([('codigo','=','HINICIODIA')], limit=1)
            if not flagInicioDia:
                raise Warning('Error: No se ha definido el parámetro "Hora Inicio Día"')
            flagInicioNoche = self.env['motgama.parametros'].search([('codigo','=','HINICIONOCHE')], limit=1)
            if not flagInicioNoche:
                raise Warning('Error: No se ha definido el parámetro "Hora Inicio Noche"')
            inicioDiaTz = datetime.strptime(str(flagInicioDia['valor']),"%H:%M")
            inicioNocheTz = datetime.strptime(str(flagInicioNoche['valor']),"%H:%M")
            fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
            if (inicioDiaTz.time() < fechaActualTz.time() < inicioNocheTz.time()):
                Lista = calendario['listapreciodia']
            else:
                Lista = calendario['listaprecionoche']
            tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search(['&',('habitacion_id','=',fullHabitacion.id),('nombrelista','=',Lista)], limit=1)
            if tarifaHabitacion:
                valorocasional = tarifaHabitacion.tarifaocasional
                valoramanecida = tarifaHabitacion.tarifamanecida
                valoradicional = tarifaHabitacion.tarifahoradicional
            else:
                tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search(['&',('tipo_id','=',fullHabitacion.tipo_id.id),('nombrelista','=',Lista)], limit=1)
                if tarifaTipoHabitacion:
                    valorocasional = tarifaTipoHabitacion.tarifaocasional
                    valoramanecida = tarifaTipoHabitacion.tarifamanecida
                    valoradicional = tarifaTipoHabitacion.tarifahoradicional
                else:
                    raise Warning('Error: No hay tarifas definidas ni para la habitación ni para el tipo de habitación')
            
            record.valorocasional = valorocasional
            record.valoramanecida = valoramanecida
            record.valoradicional = valoradicional