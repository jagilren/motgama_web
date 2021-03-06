from odoo import models, fields, api
from odoo.exceptions import Warning
import pytz
from datetime import datetime, timedelta


class MotgamaWizardHabitacion(models.TransientModel):
    _name = 'motgama.wizardhabitacion'
    _description = 'Asignacion de habitacion'
    placa = fields.Char(string='Ingrese Placa',)
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')],default='particular',required=True)
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
    
    @api.model
    def _get_observacion(self):
        idHab = self.env.context['active_id']
        hab = self.env['motgama.flujohabitacion'].browse(idHab)
        return hab.observacion

    @api.multi
    def check_placa(self):
        self.ensure_one()
        if self.placa:
            placa = self.placa.upper()
            novedadPlaca = self.env['motgama.placa'].search([('placa','=',placa)], limit=1)
            if novedadPlaca:
                msg = 'La placa ' + self.placa + ' presenta el siguiente reporte: "' + novedadPlaca.descripcion + '"'
                raise Warning(msg)
            else:
                raise Warning('La placa no presenta reportes')

    @api.multi
    def button_asignar_wizard(self):
        self.ensure_one()
        # Revisa si tiene permisos para asignar
        if not self.env.ref('motgama.motgama_asigna') in self.env.user.permisos:
            raise Warning('No tiene permitido asignar habitaciones, contacte al administrador')
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
        nroDiaAyer = (fechaActualTz - timedelta(days=1)).weekday()
        nroDiaHoy = fechaActualTz.weekday()
        calendarioAyer = self.env['motgama.calendario'].search([('diasemana','=',nroDiaAyer)], limit=1)
        calendarioHoy = self.env['motgama.calendario'].search([('diasemana','=',nroDiaHoy)], limit=1)
        if not calendarioHoy:
            raise Warning('Error: No existe calendario para el día actual')

        if calendarioAyer:
            flagInicioAmanecida = calendarioAyer.horainicioamanecida
            flagfinAmanecida = calendarioAyer.horafinamanecida
            if not flagInicioAmanecida:
                raise Warning('No se ha definido "Hora Inicio Amanecida" en el calendario del día de ayer')
            if not flagfinAmanecida:
                raise Warning('No se ha definido "Hora Fin Amanecida" en el calendario del día de ayer')
            flagInicioTz = datetime.strptime(str(flagInicioAmanecida),"%H:%M")
            flagFinTz = datetime.strptime(str(flagfinAmanecida),"%H:%M")
            flagInicio = flagInicioTz + timedelta(hours=5)
            flagFin = flagFinTz + timedelta(hours=5)
            fechaAyer = fechaActual - timedelta(days=1)
            fechaAyerTz = fechaActualTz - timedelta(days=1)
            horainicioamanecida = datetime(fechaAyer.year,fechaAyer.month,fechaAyer.day,flagInicio.hour,flagInicio.minute)
            if flagInicio > flagFin:
                horafinamanecida = datetime(fechaAyer.year,fechaAyer.month,fechaAyer.day,flagFin.hour,flagFin.minute) + timedelta(days=1)
            else:
                horafinamanecida = datetime(fechaAyer.year,fechaAyer.month,fechaAyer.day,flagFin.hour,flagFin.minute)
            if fechaActual < horafinamanecida:
                calendario = calendarioAyer
                fecha = fechaAyer
                fechaTz = fechaAyerTz
            else:
                calendario = calendarioHoy
                fecha = fechaActual
                fechaTz = fechaActualTz
        else:
            calendario = calendarioHoy
            fecha = fechaActual
            fechaTz = fechaActualTz
                
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
        flagFinInicioAmanecida = calendario.horafininicioamanecida
        if not flagInicioAmanecida:
            raise Warning('No se ha definido "Hora Inicio Amanecida" en el calendario')
        if not flagfinAmanecida:
            raise Warning('No se ha definido "Hora Fin Amanecida" en el calendario')
        if not flagFinInicioAmanecida:
            raise Warning('No se ha definido "Hora Fin Amanecida" en el calendario')
        flagInicioTz = datetime.strptime(str(flagInicioAmanecida),"%H:%M")
        flagFinTz = datetime.strptime(str(flagfinAmanecida),"%H:%M")  
        flagFinInicioTz = datetime.strptime(str(flagFinInicioAmanecida),"%H:%M")
        if self.asignatipo == 'OA':
            if flagInicioAmanecida == '0' and flagfinAmanecida == '0':
                raise Warning('No se admite amanecida')
            # CONDICION -> Horas en formato 24 horas HORAS:MINUTOS
            if flagInicioTz > flagFinInicioTz:
                if flagFinInicioTz.time() < fechaTz.time() < flagInicioTz.time():
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
            else:
                if not (flagInicioTz.time() <= fechaTz.time() <= flagFinInicioTz.time()):
                    raise Warning('Lo sentimos, no está disponible la asignación para amanecida en este momento')
        flagInicio = flagInicioTz + timedelta(hours=5)
        flagFin = flagFinTz + timedelta(hours=5)
        horainicioamanecida = datetime(fecha.year,fecha.month,fecha.day,flagInicio.hour,flagInicio.minute)
        if flagInicioTz > flagFinTz:
            horafinamanecida = datetime(fecha.year,fecha.month,fecha.day,flagFin.hour,flagFin.minute) + timedelta(days=1)
        else:
            horafinamanecida = datetime(fecha.year,fecha.month,fecha.day,flagFin.hour,flagFin.minute)
        valores.update({'horainicioamanecida':horainicioamanecida})
        valores.update({'horafinamanecida':horafinamanecida})

        # Ahora busca en las placas para verificar alguna novedad y mostrarla al operador. El mensaje aparece en el chatter
        if self.placa:
            placa = self.placa.upper()
            novedadPlaca = self.env['motgama.placa'].search([('placa','=',placa)], limit=1)
            if novedadPlaca:
                msg = 'La placa ' + self.placa + ' presenta el siguiente reporte: "' + novedadPlaca.descripcion + '"'
                title = 'Reporte de placa ' + self.placa
                if novedadPlaca.tiporeporte == 'negativo':
                    self.env.user.sudo().notify_warning(message=msg,title=title,sticky=True)
                else:
                    self.env.user.sudo().notify_success(message=msg,title=title,sticky=True)
            valores.update({'placa_vehiculo':self.placa})
            
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
        
        if flujo.prox_reserva:
            valores.update({'reserva':flujo.prox_reserva.id})
            nuevoMovimiento = self.env['motgama.movimiento'].create(valores)
            if not nuevoMovimiento:
                raise Warning('Atención! No se pudo asignar la habitación; por favor consulte con el administrador del sistema')
            recaudoAnticipo = flujo.prox_reserva.recaudo_id
            if recaudoAnticipo:
                recaudoAnticipo.sudo().write({'movimiento_id':nuevoMovimiento.id})
        else:
            nuevoMovimiento = self.env['motgama.movimiento'].create(valores)
            if not nuevoMovimiento:
                raise Warning('Atención! No se pudo asignar la habitación; por favor consulte con el administrador del sistema')
        # Si fue exitosa la creación del registro entonces se cambia el estado de la habitación
        flujo.sudo().write({
            'estado':self.asignatipo,
            'ultmovimiento':nuevoMovimiento.id,
            'prox_reserva':False,
            'notificar': True
        })
        
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