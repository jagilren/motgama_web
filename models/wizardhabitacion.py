import time
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

class MotgamaWizardHabitacion(models.TransientModel):
    _inherit = 'motgama.wizardhabitacion'

    @api.multi
    def button_asignar_wizard(self):
        self.ensure_one()
        # Extrae del contexto el ID de la habitaciòn actual
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
        
        # Esto me da el numero del día de la semana, python arranca con 0->lunes
        nroDia = fechaActualTz.weekday()
        calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
        if not calendario:
            raise Warning('Error: No existe calendario para el día actual')

        # La variable valores contendrá el diccionario de datos que se pasaran al momento de crear el registro                  #P7.0.4R
        valores = {}

        # Toma el tiempo de ocupacion normal ocasional de calendario, 
        # si tiene salvedad lo toma de la habitacion
        tiemponormal = calendario.tiemponormalocasional
        if calendario.flagignoretiempo:
            tiemponormal = fullHabitacion.tiemponormalocasional
        valores.update({'tiemponormalocasional': tiemponormal})
            
        # Verifica el tipo de asignación, si es amanecida verifica que el lugar permita amanecida               #P7.0.4R
        # Verifica tambien que se este dentro del horario permitido para asignar amanecidas
        flagInicioAmanecida = calendario.horainicioamanecida
        flagfinAmanecida = calendario.horafinamanecida
        if not flagInicioAmanecida:
            raise Warning('No se ha definido "Hora Inicio Amanecida" en el calendario')
        if not flagfinAmanecida:
            raise Warning('No se ha definido "Hora Fin Amanecida" en el calendario')   
        flagInicioTz = datetime.strptime(str(flagInicioAmanecida),"%H:%M")
        flagFinTz = datetime.strptime(str(flagfinAmanecida),"%H:%M")  
        if self.asignatipo == 'OA':
            if flagInicioAmanecida == '0' and flagfinAmanecida == '0':
                raise Warning('No se admite amanecida')
            # CONDICION -> Horas en formato 24 horas HORAS:MINUTOS
            if flagInicioTz > flagFinTz:
                if flagFinTz.time() < fechaActualTz.time() < flagInicioTz.time():
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
            else:
                if not (flagInicioTz.time() < fechaActualTz.time() < flagFinTz.time()): # OJO No incluye los extremos
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
        flagInicio = flagInicioTz + timedelta(hours=5)
        flagFin = flagFinTz + timedelta(hours=5)
        horainicioamanecida = datetime(fechaActual.year,fechaActual.month,fechaActual.day,flagInicio.hour,flagInicio.minute)
        if flagInicioTz > flagFinTz:
            horafinamanecida = datetime(fechaActual.year,fechaActual.month,fechaActual.day,flagFin.hour,flagFin.minute) + timedelta(days=1)
        else:
            horafinamanecida = datetime(fechaActual.year,fechaActual.month,fechaActual.day,flagFin.hour,flagFin.minute)
        valores.update({'horainicioamanecida':horainicioamanecida})
        valores.update({'horafinamanecida':horafinamanecida})

        # Ahora busca en las placas para verificar alguna novedad y mostrarla al operador. El mensaje aparece en el chatter
        if self.placa:
            placa = self.placa.upper()
            novedadPlaca = self.env['motgama.placa'].search([('placa','=',str(placa))], limit=1)
            if novedadPlaca:
                self.message_post(novedadPlaca['descripcion'], subject='Atención! Esta placa registra una novedad previa...',subtype='mail.mt_comment')
            valores.update({'placa_vehiculo': placa})
            
        # Se rellena el diccionario con los valores del registro
        valores.update({'habitacion_id': fullHabitacion.id})
        valores.update({'tipovehiculo': self.tipovehiculo})
        valores.update({'asignatipo': self.asignatipo})
        valores.update({'asignafecha': fechaActual})
        valores.update({'asigna_uid': self.env.user.id})
        # Se consultan las tarifas de la lista de precios que corresponde al día y la hora
        flagInicioDia = self.env['motgama.parametros'].search([('codigo','=','HINICIODIA')], limit=1)
        if not flagInicioDia:
            raise Warning('Error: No se ha definido el parámetro "Hora Inicio Día"')
        flagInicioNoche = self.env['motgama.parametros'].search([('codigo','=','HINICIONOCHE')], limit=1)
        if not flagInicioNoche:
            raise Warning('Error: No se ha definido el parámetro "Hora Inicio Noche"')
        # nombreDia = calendar.day_name[nroDia] # Utilizo el calendario para saber el nombre del día.
        inicioDiaTz = datetime.strptime(str(flagInicioDia['valor']),"%H:%M")
        inicioNocheTz = datetime.strptime(str(flagInicioNoche['valor']),"%H:%M")
        fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)

        valores.update({'listaprecioproducto':calendario['listaprecioproducto'].id})
        valores.update({'listaprecioproducto':calendario['listaprecioproducto'].id})
        if (inicioDiaTz.time() < fechaActualTz.time() < inicioNocheTz.time()):
            Lista = calendario['listapreciodia']
        else:
            Lista = calendario['listaprecionoche']

        # Chequear primero si la habitacion tiene seteada la lista de precios
        tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search(['&',('habitacion_id','=',fullHabitacion.id),('nombrelista','=',Lista)], limit=1)
        if tarifaHabitacion:
            valores.update({'tarifaocasional': tarifaHabitacion['tarifaocasional']})
            valores.update({'tarifamanecida': tarifaHabitacion['tarifamanecida']})
            valores.update({'tarifahoradicional': tarifaHabitacion['tarifahoradicional']})
        else:
            # Si la habitacion no tiene seteada unas tarifas, se procede con las que hay por tipo de habitacion            
            tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search(['&',('tipo_id','=',fullHabitacion.tipo_id.id),('nombrelista','=',Lista)], limit=1)
            if tarifaTipoHabitacion:
                valores.update({'tarifaocasional': tarifaTipoHabitacion['tarifaocasional']})
                valores.update({'tarifamanecida': tarifaTipoHabitacion['tarifamanecida']})
                valores.update({'tarifahoradicional': tarifaTipoHabitacion['tarifahoradicional']})
            else:
                # Si tampoco hay tarifas para el tipo de habitacion sale un mensaje
                # NO LO TENGO DEFINIDO
                raise Warning('Error: No hay tarifas definidas ni para la habitación ni para el tipo de habitación')
        # Si todo ha ido bien ya se puede asentar el registro del movimiento
        # Instancia la clase movimiento
        Movimiento = self.env['motgama.movimiento']
        # Crea el registro pasando el diccionario de valores como parámetro
        nuevoMovimiento = Movimiento.create(valores)
        # Si fue exitosa la creación del registro entonces se cambia el estado de la habitación
        if nuevoMovimiento:
            flujo.sudo().write({
                'estado':self.asignatipo,
                'ultmovimiento':nuevoMovimiento.id,
                'prox_reserva':False,
                'notificar': True
            })
        else:
            raise Warning('Atención! No se pudo asignar la habitación; por favor consulte con el administrador del sistema')
        
        if fullHabitacion.inmotica:
            valoresInmotica = {
                'habitacion': flujo.codigo,
                'mensaje': 'entrada',
                'evento': 'Habitación asignada'
            }
            mensajeInmotica = self.env['motgama.inmotica'].create(valoresInmotica)
            if not mensajeInmotica:
                raise Warning('Error al registrar inmótica')

        self.refresh_views()
        
        return True
        # TODO manejo de anticipo y pago de contado en negocios del centro