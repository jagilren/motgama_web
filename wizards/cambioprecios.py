from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError

#   Se instancia la clase heredada de motgama.py
class MotgamaWizardCambioPrecios(models.TransientModel):
    _name = 'motgama.wizardcambioprecios'
    _description = 'Formulario para cambiar masivamente los precios'

    @api.multi
    #   Se define la función del botón de cambio de precios
    def btn_cambiar_precios(self):
        #   Se cargan las listas de precios configuradas para las habitaciones
        ListasPreciosHabitacion = self.env['motgama.listapreciohabitacion'].search([])
        if ListasPreciosHabitacion.exists():
            #   Si existe al menos una lista de precios: Borra toda la tabla de lista de precios de Habitación
            ListasPreciosHabitacion.unlink()

        #   Se cargan los tipos de habitación
        TiposHabitacion = self.env['motgama.tipo'].search([])

        #   Se recorre cada uno de los tipos
        for tipo in TiposHabitacion:
            #   Se cargan las listas de precios y las habitaciones del tipo de habitación
            Listas = self.env['motgama.listapreciotipo'].search([('tipo_id','=',tipo.id)])
            Habitaciones = self.env['motgama.habitacion'].search([('tipo_id','=',tipo.id)])

            #   Se recorre cada habitación y cada lista de precios
            for habitacion in Habitaciones:
                for lista in Listas:
                    #   Se carga un diccionario con la información de la lista de precios
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
        
        #   TODO: Salir de la vista de actualizar precios
        #   raise Warning('Fin del proceso')
