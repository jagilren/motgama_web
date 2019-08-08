from . import motgama
from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning, ValidationError

class MotgamaWizardCambioPrecios(models.TransientModel):
    _inherit = 'motgama.wizardcambioprecios'

    @api.multi
    def btn_cambiar_precios(self):
        # raise Warning('Esta función está en otro archivo')
        ListasPreciosHabitacion = self.env['motgama.listapreciohabitacion'].search([])
        if ListasPreciosHabitacion.exists():
            ListasPreciosHabitacion.unlink() # Si existen listas de precios: Borra toda la tabla de lista de precios de Habitación
        TiposHabitacion = self.env['motgama.tipo'].search([])
        for tipo in TiposHabitacion:
            Listas = self.env['motgama.listapreciotipo'].search([('tipo_id','=',tipo.id)])
            Habitaciones = self.env['motgama.habitacion'].search([('tipo_id','=',tipo.id)])
            for habitacion in Habitaciones:
                for lista in Listas:
                    infoLista = {
                        'nombrelista':lista.nombrelista,
                        'tarifaocasional':lista.tarifaocasional,
                        'tarifamanecida':lista.tarifamanecida,
                        'tarifahoradicional':lista.tarifahoradicional,
                        'active':lista.active,
                        'habitacion_id':habitacion.id
                    }
                    self.env['motgama.listapreciohabitacion'].create(infoLista)
