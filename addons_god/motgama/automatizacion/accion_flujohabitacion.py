from odoo import models, fields, api
from odoo.exceptions import Warning

from datetime import datetime, timedelta

class MotgamaFlujohabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.model
    def check_notify(self):
        flujos = self.env['motgama.flujohabitacion'].search([('estado','in',['OO','OA','LQ','RC','R']),('notificar','=',True)])
        if not flujos:
            return True

        paramLiq = self.env['motgama.parametros'].search([('codigo','=','TIEMPOMAXLIQUI')],limit=1)
        if not paramLiq:
            raise Warning('No se ha definido el parámetro: "TIEMPOMAXLIQUI"')
        try:
            tiempoLiq = int(paramLiq.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPOMAXLIQUI" está mal definido')

        paramRec = self.env['motgama.parametros'].search([('codigo','=','TIEMPOMAXREC')],limit=1)
        if not paramRec:
            raise Warning('No se ha definido el parámetro: "TIEMPOMAXREC"')
        try:
            tiempoRec = int(paramRec.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPOMAXREC" está mal definido')

        paramAse = self.env['motgama.parametros'].search([('codigo','=','TIEMPOMAXASEO')],limit=1)
        if not paramAse:
            raise Warning('No se ha definido el parámetro: "TIEMPOMAXASEO"')
        try:
            tiempoAse = int(paramAse.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPOMAXASEO" está mal definido')

        paramFin = self.env['motgama.parametros'].search([('codigo','=','TIEMPOFINOCUP')],limit=1)
        if not paramFin:
            raise Warning('No se ha definido el parámetro: "TIEMPOFINOCUP"')
        try:
            tiempoFin = int(paramFin.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPOFINOCUP" está mal definido')

        paramRes = self.env['motgama.parametros'].search([('codigo','=','TIEMPODECRES')],limit=1)
        if not paramRes:
            raise Warning('No se ha definido el parámetro "TIEMPODECRES"')
        try:
            tiempoRes = int(paramRes.valor)
        except ValueError:
            raise Warning('El parámetro "TIEMPODECRES" está mal definido')

        fechaActual = fields.Datetime().now()

        for flujo in flujos:
            if not flujo.notificar:
                continue
            usuarios = self.env['res.users'].search([('recepcion_id','=',flujo.recepcion.id)])
            uids = [usuario.id for usuario in usuarios]
            valores = {
                'modelo': 'motgama.flujohabitacion',
                'tipo_evento': 'notificacion',
                'notificacion_uids': [(6,0,uids)]
            }
            valoresFlujo = {'notificar': False}
            notificar = False

            if flujo.estado == 'OO':
                fechaFin = flujo.ultmovimiento.asignafecha + timedelta(hours=flujo.ultmovimiento.tiemponormalocasional)
                if fechaFin > fechaActual and fechaFin - fechaActual <= timedelta(minutes=tiempoFin):
                    horaFinStr = (fechaFin - timedelta(hours=5)).strftime('%-I:%M:%S %p')
                    fechaFinStr = (fechaFin - timedelta(hours=5)).strftime('%d/%m/%Y')
                    valoresFlujo.update({'sin_alerta':False,'alerta_msg':'El hospedaje de esta habitación finaliza a la(s) ' + horaFinStr + ' del ' + fechaFinStr})
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' está próxima a terminar el tiempo ocasional',
                        'descripcion': 'La habitación ' + flujo.codigo + ' terminará su tiempo ocasional en ' + str(tiempoFin) + ' minutos'
                    })
                    notificar = True
                elif fechaActual > fechaFin:
                    valoresFlujo.update({'sin_alerta':True,'alerta_msg':''})

            elif flujo.estado == 'OA':
                fechaFin = flujo.ultmovimiento.horafinamanecida
                if fechaFin > fechaActual and fechaFin - fechaActual <= timedelta(minutes=tiempoFin):
                    horaFinStr = (fechaFin - timedelta(hours=5)).strftime('%-I:%M:%S %p')
                    fechaFinStr = (fechaFin - timedelta(hours=5)).strftime('%d/%m/%Y')
                    valoresFlujo.update({'sin_alerta':False,'alerta_msg':'El hospedaje de esta habitación finaliza a la(s) ' + horaFinStr + ' del ' + fechaFinStr})
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' está próxima a terminar el tiempo de amanecida',
                        'descripcion': 'La habitación ' + flujo.codigo + ' terminará su tiempo de amanecida en ' + str(tiempoFin) + ' minutos'
                    })
                    notificar = True
                elif fechaActual > fechaFin:
                    valoresFlujo.update({'sin_alerta':True,'alerta_msg':''})

            elif flujo.estado == 'LQ':
                if flujo.lq and tiempoLiq != 0:
                    if fechaActual - flujo.ultmovimiento.liquidafecha >= timedelta(minutes=tiempoRec):
                        valoresFlujo.update({'sin_alerta':False,'alerta_msg':'Esta habitación lleva mucho tiempo liquidada y debe ser recaudada inmediatamente'})
                        valoresFlujo.update({'lq':False})
                        valores.update({
                            'asunto': 'Habitación ' + flujo.codigo + ' debe ser recaudada inmediatamente',
                            'descripcion': 'La habitación ' + flujo.codigo + ' lleva ' + str(tiempoRec) + ' minutos liquidada y debe ser recaudada inmediatamente'
                        })
                        notificar = True
                elif tiempoLiq != 0:
                    if fechaActual - flujo.ultmovimiento.liquidafecha >= timedelta(minutes=tiempoLiq):
                        valoresFlujo.update({'sin_alerta':False,'alerta_msg':'Esta habitación lleva mucho tiempo liquidada y se debe recaudar o continuar la asignación'})
                        valoresFlujo.update({'lq':True,'notificar':True})
                        valores.update({
                            'asunto': 'Habitación ' + flujo.codigo + ' debe ser recaudada o rehabilitada',
                            'descripcion': 'La habitación ' + flujo.codigo + ' lleva ' + str(tiempoLiq) + ' minutos liquidada y se debe recaudar o continuar la asignación'
                        })
                        notificar = True
                else:
                    valoresFlujo.update({'sin_alerta':True,'alerta_msg':''})
                    notificar = False
            
            elif flujo.estado == 'RC':
                if flujo.ultmovimiento.recaudafecha:
                    fechaAseo = flujo.ultmovimiento.recaudafecha
                elif flujo.ultmovimiento.desasignafecha:
                    fechaAseo = flujo.ultmovimiento.desasignafecha
                elif flujo.ultmovimiento.aseofecha:
                    fechaAseo = flujo.ultmovimiento.aseofecha
                elif len(flujo.ultmovimiento.reasignaciones) > 0:
                    for reasignacion in flujo.ultmovimiento.reasignaciones:
                        if reasignacion.habitacion_anterior.id == flujo.id:
                            fechaAseo = reasignacion.fechareasigna
                            break
                        else:
                            fechaAseo = False
                    if not fechaAseo:
                        continue
                else:
                    continue
                if fechaActual - fechaAseo >= timedelta(minutes=tiempoAse):
                    valoresFlujo.update({'sin_alerta':False,'alerta_msg':'Esta habitación lleva mucho tiempo en Aseo y debe ser habilitada nuevamente'})
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' debe ser habilitada',
                        'descripcion': 'La habitación ' + flujo.codigo + ' lleva ' + str(tiempoAse) + ' minutos en estado Aseo y debe ser habilitada nuevamente'
                    })
                    notificar = True
            
            elif flujo.estado == 'R':
                if flujo.prox_reserva.condecoracion and flujo.prox_reserva.fecha - fechaActual <= timedelta(hours=tiempoRes):
                    horaResStr = (flujo.prox_reserva.fecha - timedelta(hours=5)).strftime('%-I:%M:%S %p')
                    fechaResStr = (flujo.prox_reserva.fecha - timedelta(hours=5)).strftime('%d/%m/%Y')
                    valoresFlujo.update({'sin_alerta':False,'alerta_msg':'Esta habitación debe ser decorada antes de las ' + horaResStr + ' del ' + fechaResStr})
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' debe ser decorada para dentro de ' + str(tiempoRes) + ' horas',
                        'descripcion': 'La habitación ' + flujo.codigo + ' está reservada para dentro de ' + str(tiempoRes) + ' horas, es necesario iniciar la decoración contratada'
                    })
                    notificar = True
            else:
                valoresFlujo.update({'sin_alerta':True,'alerta_msg':''})
                flujo.write({'notificar':False})
                continue
            
            if notificar:
                flujo.write(valoresFlujo)
                notificacion = self.env['motgama.log'].create(valores)
                if not notificacion:
                    raise Warning('No se pudo crear la notificación con asunto: "' + valores['asunto'] + '"')