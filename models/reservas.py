from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaReservas(models.Model):
    _inherit = 'motgama.reserva'

    @api.model
    def create(self,values):
        record = super().create(values)
        record.esNueva = False
        record.cod = str(record.id)
        return record
    
    @api.multi
    def button_modificar(self):
        pass

    @api.multi
    def button_cancelar(self):
        pass