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
            raise Warning('El usuario no tiene una zona horaria definida, contacte al administrador')
        
        tz = pytz.timezone(self.env.user.tz)

        # Verifica el tipo de asignación, si es amanecida verifica que el lugar permita amanecida
        # Verifica tambien que se este dentro del horario permitido para asignar amanecidas      
        if self.asignatipo == 'OA':
            flagInicioAmanecida = self.env['motgama.parametros'].search([('codigo','=','HINIAMANECIDA')], limit=1)
            flagfinAmanecida = self.env['motgama.parametros'].search([('codigo','=','HFINAMANECIDA')], limit=1)
            if not flagInicioAmanecida:
                raise Warning('No se ha definido el parámetro "Hora Inicio Amanecida"')
            if not flagfinAmanecida:
                raise Warning('No se ha definido el parámetro "Hora Fin Amanecida"')
            if flagInicioAmanecida['valor'] == '0' and flagfinAmanecida['valor'] == '0':
                raise Warning('No se admite amanecida')
            # CONDICION -> Horas en formato 24 horas HORAS:MINUTOS
            flagInicioTz = datetime.strptime(str(flagInicioAmanecida['valor']),"%H:%M")
            flagFinTz = datetime.strptime(str(flagfinAmanecida['valor']),"%H:%M")
            flagInicio = tz.localize(flagInicioTz).astimezone(pytz.utc).time()
            flagFin = tz.localize(flagFinTz).astimezone(pytz.utc).time()
            if flagInicio > flagFin:
                if flagFin < fechaActual.time() < flagInicio:
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
            else:
                if not (flagInicio < fechaActual.time() < flagFin): # OJO No incluye los extremos
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
        # Ahora busca en las placas para verificar alguna novedad y mostrarla al operador. El mensaje aparece en el chatter
        novedadPlaca = self.env['motgama.placa'].search([('placa','=',str(self.placa))], limit=1)
        if novedadPlaca:
            self.message_post(novedadPlaca['descripcion'], subject='Atención! Esta placa registra una novedad previa...',subtype='mail.mt_comment')
        # La variable valores contendrá el diccionario de datos que se pasaran al momento de crear el registro
        valores = {}
        # Se rellena el diccionario con los valores del registro
        valores.update({'habitacion_id': fullHabitacion.id})
        valores.update({'tipovehiculo': self.tipovehiculo})
        valores.update({'placa_vehiculo': self.placa})
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
        # nroDia = datetime.strptime(fechaActual.date(), '%d %m %Y').weekday() # Esto me da el numero del día de la semana, python arranca con 0->lunes
        nroDia = fechaActual.weekday()
        # nombreDia = calendar.day_name[nroDia] # Utilizo el calendario para saber el nombre del día.
        inicioDiaTz = datetime.strptime(str(flagInicioDia['valor']),"%H:%M")
        inicioDia = tz.localize(inicioDiaTz).astimezone(pytz.utc).time()
        inicioNocheTz = datetime.strptime(str(flagInicioNoche['valor']),"%H:%M")
        inicioNoche = tz.localize(inicioNocheTz).astimezone(pytz.utc).time()
        qryLista = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
        if qryLista:
            if (inicioDia < fechaActual.time() < inicioNoche):
                Lista = qryLista['listapreciodia']
            else:
                Lista = qryLista['listaprecionoche']
        else:
            raise Warning('Error: No existe calendario para la lista de precios')
        # Chequear primero si la habitacion tiene seteada la lista de precios
        tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search([('habitacion_id','=',Habitacion),('nombrelista','=',Lista)], limit=1)
        if tarifaHabitacion:
            valores.update({'tarifaocasional': tarifaHabitacion['tarifaocasional']})
            valores.update({'tarifamanecida': tarifaHabitacion['tarifamanecida']})
            valores.update({'tarifahoradicional': tarifaHabitacion['tarifahoradicional']})
        else:
            # Si la habitacion no tiene seteada unas tarifas, se procede con las que hay por tipo de habitacion            
            tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search([('tipo_id','=',fullHabitacion['tipo_id'].id),('nombrelista','=',Lista)], limit=1)
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
            flujo.sudo().write({'estado':self.asignatipo})
        else:
            raise Warning('Atención! No se pudo asignar la habitación; por favor consulte con el administrador del sistema')
        #Termina
        return True # Esta instruccion no es estrictamente necesaria pero es una buena práctica.
        # POR REVISSAR