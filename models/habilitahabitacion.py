from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_habilita(self):
        self.ensure_one()
        movimiento = self.ultmovimiento

        fechaActual = datetime.now()  # coloca la fecha y hora en que se habilita la habitacion
        
        if movimiento:      # modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion      #P7.0.4R
            valores = {'habilitafecha':fechaActual,
                        'habilita_uid':self.env.user.id,
                        'active':False}
            movimiento.write(valores)
            self.write({'estado':'D'}) # pone en estado disponible
        else:
            raise Warning('No se pudo cambiar el estado para habilitar la habitación')

        self.refresh_views()
        
        return True