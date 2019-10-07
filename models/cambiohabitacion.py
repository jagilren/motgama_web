import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning

class MotgamaWizardCambiohabitacion(models.TransientModel):
    _inherit = 'motgama.wizardcambiohabitacion'

    @api.multi
    def button_cambio_habitacion(self):
        self.ensure_one()
        flujo_id = self.env.context['active_id']
        flujo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        movimiento = flujo.ultmovimiento

        # busca la nueva habitacion y valida que se encuentre en estado disponible                      #P7.0.4R
        habitacion = self.env['motgama.habitacion'].search([('codigo','=',self.flujoNuevo.codigo)])  
        if not habitacion:
            raise Warning('No encuentra informacion de la nueva habitacion-'+self.flujoNuevo.codigo)
                     
        if self.flujoNuevo.estado != 'D':
            raise Warning('La habitación debe estar en estado disponible-'+self.flujoNuevo.estado)

        fechaActual = datetime.now()
        if not self.env.user.tz:
            tz = pytz.timezone('America/Bogota')
        else:
            tz = pytz.timezone(self.env.user.tz)
        # Esto me da el numero del dia de la semana, python arranca con 0->lunes
        # se va a tomar el calendario con la hora de asignacion y no la hora actual
        # fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz)
        fechaActualTz = pytz.utc.localize(movimiento.asignafecha).astimezone(tz)
        nroDia = fechaActualTz.weekday()
        calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
        if not calendario:
            raise Warning('Error: no existe calendario para el dia actual ',int(nroDia))

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
        # fechaActualTz = pytz.utc.localize(fechaActual).astimezone(tz) # ya esta arriba

        # La variable valores contendrá el diccionario de datos que se pasaran al momento de crear el registro                  #P7.0.4R
        valores = {}
        valores.update({'listaprecioproducto':calendario['listaprecioproducto'].id})
        if (inicioDiaTz.time() < fechaActualTz.time() < inicioNocheTz.time()):
            Lista = calendario['listapreciodia']
        else:
            Lista = calendario['listaprecionoche']

        # Chequear primero si la habitacion tiene seteada la lista de precios
        tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search(['&',('habitacion_id','=',habitacion.id),('nombrelista','=',Lista)], limit=1)
        if tarifaHabitacion:
            tarifao = tarifaHabitacion.tarifaocasional
            tarifaa = tarifaHabitacion.tarifamanecida
            tarifaha = tarifaHabitacion.tarifahoradicional
            # valores.update({'tarifaocasional': tarifaHabitacion['tarifaocasional']})
            # valores.update({'tarifamanecida': tarifaHabitacion['tarifamanecida']})
            # valores.update({'tarifahoradicional': tarifaHabitacion['tarifahoradicional']})
        else:
            # Si la habitacion no tiene seteada unas tarifas, se procede con las que hay por tipo de habitacion            
            tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search(['&',('tipo_id','=',habitacion.tipo_id.id),('nombrelista','=',Lista)], limit=1)
            if tarifaTipoHabitacion:
                tarifao = tarifaTipoHabitacion.tarifaocasional
                tarifaa = tarifaTipoHabitacion.tarifamanecida
                tarifaha = tarifaTipoHabitacion.tarifahoradicional
                # valores.update({'tarifaocasional': tarifaTipoHabitacion['tarifaocasional']})
                # valores.update({'tarifamanecida': tarifaTipoHabitacion['tarifamanecida']})
                # valores.update({'tarifahoradicional': tarifaTipoHabitacion['tarifahoradicional']})
            else:
                # Si tampoco hay tarifas para el tipo de habitacion sale un mensaje
                # NO LO TENGO DEFINIDO
                raise Warning('Error: No hay tarifas definidas ni para la habitación ni para el tipo de habitación')

        # Valida si se puede reasignar a una habitacion de menor precio
        flagReasignaMenor = self.env['motgama.parametros'].search([('codigo','=','SIREAGHABMENORPRECIO')], limit=1)
        if not flagReasignaMenor:
            raise Warning('Error: No se ha definido el parámetro "Permite reasignar habitación de menor precio"')
        if flagReasignaMenor == 'N':
            if flujo.estado == 'OO' and tarifao < movimiento.tarifaocasional:
                raise Warning('Error: No puede reasignar a una habitación de menor valor $'+int(tarifaocasional))
            else:
                if flujo.estado == 'OA' and tarifaa < movimiento.tarifamanecida:
                    raise Warning('Error: No puede reasignar a una habitación de menor valor $'+int(tarifamanecida))

        # Si todo ha ido bien ya se puede asentar el cambio en el registro del movimiento
        # Se rellena el diccionario con los valores del registro

        valores.update({'habitacion_id': habitacion.id})
        valores.update({'tarifaocasional': tarifao})
        valores.update({'tarifamanecida': tarifaa})
        valores.update({'tarifahoraadicional': tarifaha})
        valores.update({'flagreasignada': True})

        # actualiza el registro pasando el diccionario de valores como parámetro
        nuevoMovimiento = movimiento.write(valores)
        if not nuevoMovimiento:
            raise Warning('Error: No se pudo actualizar la reasignacion en movimiento')

        # actualiza el flujo de la nueva habitacion
        self.flujoNuevo.sudo().write({'estado':flujo.estado})
        self.flujoNuevo.sudo().write({'ultmovimiento':flujo.ultmovimiento.id})
        self.flujoNuevo.sudo().write({'fecha':flujo.fecha})

        # actualiza el flujo de la habitacion anterior
        flujo.sudo().write({'estado':'RC'})
        flujo.sudo().write({'fecha':datetime})

        # crea el registro de trazabilidad en reasignaciones
        Reasignacion = self.env['motgama.reasignacion']

        valoresReasigna = {}
        valoresReasigna.update({'habitacion_id':flujo.codigo})
        valoresReasigna.update({'movimiento_id':flujo.ultmovimiento.id})
        valoresReasigna.update({'fechareasigna':fechaActual})
        valoresReasigna.update({'habitacion_nueva':self.flujoNuevo.codigo})
        valoresReasigna.update({'descripcion':self.observacion})
        valoresReasigna.update({'active':True})
        nuevaReasignacion = Reasignacion.create(valoresReasigna)
        if not nuevaReasignacion:
            raise Warning('Error: No se pudo actualizar el registro de la reasignacion')
