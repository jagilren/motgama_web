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
        flujoViejo = self.env['motgama.flujohabitacion'].search([('id','=',flujo_id)])
        movimiento = flujoViejo.ultmovimiento
        flujoNuevo = self.flujoNuevo
        fullHabitacion = self.env['motgama.habitacion'].search([('codigo','=',flujoNuevo.codigo)])

        if not self.env.user.tz:
            tz = pytz.timezone('America/Bogota')
        else:
            tz = pytz.timezone(self.env.user.tz)

        fechaAsignacion = movimiento.asignafecha
        fechaAsignacionTz = pytz.utc.localize(fechaAsignacion).astimezone(tz)
        nroDia = (fechaAsignacionTz).weekday()
        calendario = self.env['motgama.calendario'].search([('diasemana','=',nroDia)], limit=1)
        if not calendario:
            raise Warning('Error: No existe calendario del día: ' + str((fechaAsignacionTz).date()))

        flagInicioDia = self.env['motgama.parametros'].search([('codigo','=','HINICIODIA')], limit=1)
        if not flagInicioDia:
            raise Warning('Error: No se ha definido el parámetro "Hora Inicio Día"')
        flagInicioNoche = self.env['motgama.parametros'].search([('codigo','=','HINICIONOCHE')], limit=1)
        if not flagInicioNoche:
            raise Warning('Error: No se ha definido el parámetro "Hora Inicio Noche"')
        inicioDiaTz = datetime.strptime(str(flagInicioDia['valor']),"%H:%M")
        inicioNocheTz = datetime.strptime(str(flagInicioNoche['valor']),"%H:%M")

        if (inicioDiaTz.time() < fechaAsignacionTz.time() < inicioNocheTz.time()):
            Lista = calendario['listapreciodia']
        else:
            Lista = calendario['listaprecionoche']

        tarifaHabitacion = self.env['motgama.listapreciohabitacion'].search(['&',('habitacion_id','=',fullHabitacion.id),('nombrelista','=',Lista)], limit=1)
        if tarifaHabitacion:
            tarifaocasional = tarifaHabitacion['tarifaocasional']
            tarifamanecida = tarifaHabitacion['tarifamanecida']
        else:           
            tarifaTipoHabitacion = self.env['motgama.listapreciotipo'].search(['&',('tipo_id','=',fullHabitacion.tipo_id.id),('nombrelista','=',Lista)], limit=1)
            if tarifaTipoHabitacion:
                tarifaocasional = tarifaTipoHabitacion['tarifaocasional']
                tarifamanecida = tarifaTipoHabitacion['tarifamanecida']
            else:
                raise Warning('Error: No hay tarifas definidas ni para la habitación nueva ni para el tipo de habitación')

        if movimiento.asignatipo == 'OO':
            if tarifaocasional < movimiento.tarifaocasional:
                if not self.env.user.motgama_reasigna_menor:
                    raise Warning('No tiene permisos para cambiar la asignación de una habitación a una de menor precio')
            else:
                if not self.env.user.motgama_reasigna_mayor:
                    raise Warning('No tiene permisos para reasignar una habitación')
        elif movimiento.asignatipo == 'OA':
            if tarifamanecida < movimiento.tarifamanecida:
                if not self.env.user.motgama_reasigna_menor:
                    raise Warning('No tiene permisos para cambiar la asignación de una habitación a una de menor precio')
            else:
                if not self.env.user.motgama_reasigna_mayor:
                    raise Warning('No tiene permisos para reasignar una habitación')
        else:
            raise Warning('Hay un problema con la asignación de la habitación')

        valoresMovto = {
            'habitacion_id': fullHabitacion.id,
            'tarifaocasional': tarifaocasional,
            'tarifamanecida': tarifamanecida,
            'tarifahoradicional': tarifaHabitacion['tarifahoradicional'],
            'flagreasignada': True,
            'observacion': self.observacion
        }
        movtoguardado = movimiento.write(valoresMovto)
        if not movtoguardado:
            raise Warning('No se pudo actualizar el movimiento de asignación')

        valoresNuevo = {
            'estado': flujoViejo.estado,
            'ultmovimiento': movimiento.id
        }
        nuevoguardado = flujoNuevo.write(valoresNuevo)
        if not nuevoguardado:
            raise Warning('No se pudo asignar la nueva habitación')

        valoresViejo = {
            'estado': 'RC',
            'notificar':True
        }
        viejoguardado = flujoViejo.write(valoresViejo)
        if not viejoguardado:
            raise Warning('No se pudo actualizar la habitación anterior')

        valoresReasignacion = {
            'habitacion_anterior': flujoViejo.id,
            'movimiento_id': movimiento.id,
            'habitacion_nueva': flujoNuevo.id,
            'descripcion': self.observacion
        }
        nuevaReasignacion = self.env['motgama.reasignacion'].create(valoresReasignacion)
        if not nuevaReasignacion:
            raise Warning('No se pudo crear el registro de reasignación')

        hab1 = self.env['motgama.habitacion'].search([('codigo','=',flujoViejo.codigo)],limit=1)
        if not hab1:
            raise Warning('Error al cargar la habitación anterior')
        hab2 = self.env['motgama.habitacion'].search([('codigo','=',flujoNuevo.codigo)],limit=1)
        if not hab2:
            raise Warning('Error al cargar la nueva habitación')

        if hab1.inmotica:
            valoresInmotica1 = {
                'habitacion': flujoViejo.codigo,
                'mensaje': 'salida',
                'evento': 'Cambio de habitación a la ' + flujoNuevo.codigo
            }
            mensajeInmotica1 = self.env['motgama.inmotica'].create(valoresInmotica1)
            if not mensajeInmotica1:
                raise Warning('Error al registrar inmótica')

        if hab2.inmotica:
            valoresInmotica2 = {
                'habitacion': flujoNuevo.codigo,
                'mensaje': 'entrada',
                'evento': 'Cambio de habitación de la ' + flujoViejo.codigo
            }
            mensajeInmotica2 = self.env['motgama.inmotica'].create(valoresInmotica2)
            if not mensajeInmotica2:
                raise Warning('Error al registrar inmótica')
        
        valores = {
            'fecha': fields.Datetime().now(),
            'modelo': 'motgama.wizardcambiohabitacion',
            'tipo_evento': 'correo',
            'asunto': 'El hospedaje de la habitación ' + flujoViejo.codigo + ' ha sido trasladado a la habitación ' + flujoNuevo.codigo,
            'descripcion': 'El usuario ' + self.env.user.name + ' ha trasladado el hospedaje de la habitación ' + flujoViejo.codigo + ' a la habitación ' + flujoNuevo.codigo + '. Observaciones: ' + str(self.observacion)
        }
        self.env['motgama.log'].create(valores)

        self.refresh_views()
        
        return True
