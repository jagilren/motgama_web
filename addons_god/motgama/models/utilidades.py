from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError

#   Se instancia la clase heredada de motgama.py
class MotgamaUtilidades(models.TransientModel):
    _inherit = 'motgama.utilidades'

    @api.multi
    def btn_cambio_recepcion(self):
        nueva_recepcion = self.nueva_recepcion
        if not nueva_recepcion:
            raise Warning('Seleccione una recepción')
        if self.env.user.recepcion_id.id == nueva_recepcion.id:
            raise ValidationError('Ya se encuentra en esta recepción')
        else:
            self.env.user.write({'recepcion_id': nueva_recepcion.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.flujohabitacion',
            'name': 'Habitaciones ' + self.env.user.recepcion_id.nombre,
            'view_mode': 'kanban',
            'limit': 100,
            'domain': [('recepcion','=',self.env.user.recepcion_id.id)],
            'target': 'main'
        }

    @api.multi
    #   Se define la función del botón de cambio de precios
    def btn_cambiar_precios(self):
        if not self.env.ref('motgama.motgama_cambia_precios') in self.env.user.permisos:
            raise Warning('No tiene permitido cambiar de forma masiva los precios de las habitaciones, contacte al administrador')
        #   Se cargan las listas de precios configuradas para las habitaciones
        ListasPreciosHabitacion = self.env['motgama.listapreciohabitacion'].search([])
        if ListasPreciosHabitacion.exists():
            #   Si existe al menos una lista de precios: Borra toda la tabla de lista de precios de Habitación
            ListasPreciosHabitacion.unlink()

        #   Se cargan los tipos de habitación                                                                           P7.0.4R
        TiposHabitacion = self.env['motgama.tipo'].search([])

        #   Se recorre cada uno de los tipos
        for tipo in TiposHabitacion:
            #   Se cargan las listas de precios y las habitaciones del tipo de habitación
            Listas = self.env['motgama.listapreciotipo'].search([('tipo_id','=',tipo.id)])
            Habitaciones = self.env['motgama.habitacion'].search([('tipo_id','=',tipo.id)])

            #   Se recorre cada habitación y cada lista de precios
            for habitacion in Habitaciones:
                for lista in Listas:
                    #   Se carga un diccionario con la información de la lista de precios                               P7.0.4R
                    infoLista = {
                        'nombrelista':lista.nombrelista,
                        'tarifaocasional':lista.tarifaocasional,
                        'tarifamanecida':lista.tarifamanecida,
                        'tarifahoradicional':lista.tarifahoradicional,
                        'active':lista.active,
                        'habitacion_id':habitacion.id
                    }

                    #   Se graba la información cargada de la lista de precios del tipo en la tabla de lista de precios de habitación
                    self.env['motgama.listapreciohabitacion'].create(infoLista)
                # actualiza el numero de horas para el hospedaje ocasional
                habitacion.write({'tiemponormalocasional':tipo.tiemponormalocasional})
        
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Procesa de cambiar listas de precio y tiempo normal ocasional finalizado'
        return {
            'name': 'Proceso completo',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id,'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }
