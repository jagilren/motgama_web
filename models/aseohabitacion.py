from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_aseo(self):
        self.ensure_one()
        movimiento = self.ultmovimiento

        fechaActual = datetime.now()  # coloca la fecha y hora en que se habilita la habitacion

        if movimiento:      # modifica el estado para poner en aseo y poder habilitar nuevamente la habitacion  #P7.0.4R
            valores = {'aseofecha':fechaActual,
                        'aseo_uid':self.env.user.id}
            movimiento.write(valores)
            self.sudo().write({'estado':'RC'}) # pone en estado disponible
        else:
            raise Warning('No se pudo cambiar el estado para asear la habitación')