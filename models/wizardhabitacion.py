class MotgamaWizardHabitacion(models.TransientModel):
    _inherit = 'motgama.wizardhabitacion'

    @api.multi
    def button_asignar_wizard(self):
        self.ensure_one()
        # Extrae del contexto el ID de la habitaciòn actual
        Habitacion = self.env.context['active_id']
        fullHabitacion = self.env['motgama.habitacion'].search([('id','=',Habitacion)], limit=1) # Trae todos los datos de la habitacion actual        
        fechaActual = datetime.datetime.now().date()
        horaActual = datetime.datetime.now().time()
        # Verifica el tipo de asignación, si es amanecida verifica que el lugar permita amanecida
        # Verifica tambien que se este dentro del horario permitido para asignar amanecidas      
        if self.asignatipo == 'OA':
            flagAmanecida = self.env['motgama.parametros'].search([('name','=','Permite Amanecida?')], limit=1)
            if flagAmanecida['valor'] == 'NO':
                raise Warning('Lo sentimos, este lugar no permite amanecida!')
            # CONDICION -> Horas en formato militar por favor HORAS:MINUTOS:SEGUNDOS
            flagInicioAmanecida = self.env['motgama.parametros'].search([('name','=','Hora Inicio Amanecida?')], limit=1)
            flagfinAmanecida = self.env['motgama.parametros'].search([('name','=','Hora Fin Amanecida?')], limit=1)
            if not (flagInicioAmanecida['valor'] < horaActual < flagfinAmanecida['valor']): # OJO No incluye los extremos
                raise Warning('Lo sentimos, no esta disponible la asignación para amanecida en este momento!')
        # Ahora busca en las placas para verificar alguna novedad y mostrarla al operador. El mensaje aparece en el chatter
        novedadPlaca = self.env['motgama.placa'].search([('placa','=',str(self.placa))], limit=1)
        if novedadPlaca:
            self.message_post(novedadPlaca['descripcion'], subject='Atención! Esta placa registra una novedad previa...',subtype='mail.mt_comment')
        # La variable valores contendrá el diccionario de datos que se pasaran al momento de crear el registro
        valores = {}
        # Se rellena el diccionario con los valores del registro
        valores.update({'habitacion_id': Habitacion})
        valores.update({'tipovehiculo': self.tipovehiculo})
        valores.update({'placa_vehiculo': self.placa})
        valores.update({'asignatipo': asignatipo})
        valores.update({'asignafecha': fechaActual})
        valores.update({'asignahora': horaActual})
        valores.update({'asigna_uid': uid})
        # Se consultan las tarifas de la lista de precios que corresponde al día y la hora
        flagInicioDia = self.env['motgama.parametros'].search([('name','=','Hora Inicio Dia')], limit=1)
        flagInicioNoche = self.env['motgama.parametros'].search([('name','=','Hora Inicio Noche')], limit=1)
        nroDia = datetime.datetime.strptime(fechaActual, '%d %m %Y').weekday() # Esto me da el numero del día de la semana, python arranca con 0->lunes
        # nombreDia = calendar.day_name[nroDia] # Utilizo el calendario para saber el nombre del día.
        qryLista = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
        if qryLista:
            if (flagInicioDia['valor'] < horaActual < flagInicioNoche['valor']):
                Lista = qryLista['listapreciodia']
            else:
                Lista = qryLista['listaprecionoche']
        else:
            raise Warning('Error! No existe lista de precios para hoy')
        # Chequear primero si la habitacion tiene seteada la lista de precios
        tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search([('habitacion_id','=',Habitacion),('nombrelista','=',Lista)], limit=1)
        if tarifaHabitacion:
            valores.update({'tarifaocasional': tarifaHabitacion['tarifaocasional']})
            valores.update({'tarifamanecida': tarifaHabitacion['tarifamanecida']})
            valores.update({'tarifahoradicional': tarifaHabitacion['tarifahoradicional']})
        else:
            # Si la habitacion no tiene seteada unas tarifas, se procede con las que hay por tipo de habitacion            
            tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search([('tipo_id','=',fullHabitacion['tipo_id']),('nombrelista','=',Lista)], limit=1)
            if tarifaTipoHabitacion:
                valores.update({'tarifaocasional': tarifaTipoHabitacion['tarifaocasional']})
                valores.update({'tarifamanecida': tarifaTipoHabitacion['tarifamanecida']})
                valores.update({'tarifahoradicional': tarifaTipoHabitacion['tarifahoradicional']})
            else:
                # Si tampoco hay tarifas para el tipo de habitacion se procede con las del sistema
                # NO LO TENGO DEFINIDO
                raise Warning('Atención! No hay tarifas definidas ni para la habitación ni para el tipo de habitación')
        # Si todo ha ido bien ya se puede asentar el registro del movimiento
        # Instancia la clase movimiento
        Movimiento = self.env['motgama.movimiento']
        # Crea el registro pasando el diccionario de valores como parámetro
        nuevoMovimiento = Movimiento.create(valores)
        # Si fue exitosa la creación del registro entonces se cambia el estado de la habitación
        if nuevoMovimiento:
            fullHabitacion.sudo().write({'estado':asignatipo})
        else:
            raise Warning('Atención! No se pudo asignar la habitación; por favor consulte con el administrador del sistema')
        #Termina
        return True # Esta instruccion no es estrictamente necesaria pero es una buena práctica.
        # POR REVISSAR