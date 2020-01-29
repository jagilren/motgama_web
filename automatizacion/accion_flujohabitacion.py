from odoo import models, fields, api
from odoo.exceptions import Warning

from datetime import timedelta

class MotgamaFlujohabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.model
    def check_notify(self):
        flujos = self.env['motgama.flujohabitacion'].search([('estado','in',['OO','OA','LQ','RC','R']),('notificar','=',True)])
        if not flujos:
            pass

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
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' está próxima a terminar el tiempo ocasional',
                        'descripcion': 'La habitación ' + flujo.codigo + ' terminará su tiempo ocasional en ' + str(tiempoFin) + ' minutos'
                    })
                    notificar = True

            elif flujo.estado == 'OA':
                fechaFin = flujo.ultmovimiento.horafinamanecida
                if fechaFin > fechaActual and fechaFin - fechaActual <= timedelta(minutes=tiempoFin):
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' está próxima a terminar el tiempo de amanecida',
                        'descripcion': 'La habitación ' + flujo.codigo + ' terminará su tiempo de amanecida en ' + str(tiempoFin) + ' minutos'
                    })
                    notificar = True

            elif flujo.estado == 'LQ':
                if flujo.lq:
                    if fechaActual - flujo.ultmovimiento.liquidafecha >= timedelta(minutes=tiempoRec):
                        valoresFlujo.update({'lq':False})
                        valores.update({
                            'asunto': 'Habitación ' + flujo.codigo + ' debe ser recaudada inmediatamente',
                            'descripcion': 'La habitación ' + flujo.codigo + ' lleva ' + str(tiempoRec) + ' minutos liquidada y debe ser recaudada inmediatamente'
                        })
                        notificar = True
                else:
                    if fechaActual - flujo.ultmovimiento.liquidafecha >= timedelta(minutes=tiempoLiq):
                        valoresFlujo.update({'lq':True,'notificar':True})
                        valores.update({
                            'asunto': 'Habitación ' + flujo.codigo + ' debe ser recaudada o rehabilitada',
                            'descripcion': 'La habitación ' + flujo.codigo + ' lleva ' + str(tiempoLiq) + ' minutos liquidada y debe ser recaudada o rehabilitada'
                        })
                        notificar = True
            
            elif flujo.estado == 'RC':
                if fechaActual - flujo.ultmovimiento.recaudafecha >= timedelta(minutes=tiempoAse):
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' debe ser habilitada',
                        'descripcion': 'La habitación ' + flujo.codigo + ' lleva ' + str(tiempoAse) + ' minutos en estado Aseo y debe ser habilitada nuevamente'
                    })
                    notificar = True
            
            elif flujo.estado == 'R':
                if flujo.prox_reserva.condecoracion and flujo.prox_reserva.fecha - fechaActual <= timedelta(hours=tiempoRes):
                    valores.update({
                        'asunto': 'Habitación ' + flujo.codigo + ' debe ser decorada para dentro de ' + str(tiempoRes) + ' horas',
                        'descripcion': 'La habitación ' + flujo.codigo + ' está reservada para dentro de ' + str(tiempoRes) + ' horas, es necesario iniciar la decoración contratada'
                    })
                    notificar = True
            else:
                flujo.write({'notificar':False})
                continue
            
            if notificar:
                flujo.write(valoresFlujo)
                notificacion = self.env['motgama.log'].create(valores)
                if not notificacion:
                    raise Warning('No se pudo crear la notificación con asunto: "' + valores['asunto'] + '"')
