from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def aplicar_bono(self):
        self.ensure_one()

        return {
            'name': 'Aplicar bono',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.bono',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_bonos').id,
            'target': 'new'
        }

class MotgamaWizardBonos(models.TransientModel):
    _name = 'motgama.wizard.bono'
    _description = 'Wizard Bonos'

    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    codigo = fields.Char(string='Código del bono')
    inf_bono = fields.Many2many(string='Información del bono', comodel_name='motgama.bonos')
    bono_valido = fields.Boolean(string='Bono validado', default=False)
    bono = fields.Many2one(string='Bono',comodel_name='motgama.bonos')
    validar = fields.Boolean(string='Validar', default=False)

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.onchange('validar')
    def _onchange_validar(self):
        for record in self:
            if record.validar:
                bono = self.env['motgama.bonos'].search([('codigo','=',self.codigo)], limit=1)
                if not bono:
                    record.validar = False
                    raise Warning('El bono no existe o ha sido desactivado')

                if fields.Date().today() < bono.validodesde:
                    record.validar = False
                    raise Warning('El bono no está disponible todavía, válido desde: ' + str(bono.validodesde))
                elif fields.Date().today() > bono.validohasta:
                    record.validar = False
                    raise Warning('El bono se ha vencido, válido hasta: ' + str(bono.validohasta))

                if bono.maximo_uso != 0 and bono.usos >= bono.maximo_uso:
                    record.validar = False
                    raise Warning('El bono ya cumplió su límite de usos, Cantidad máxima: ' + str(bono.maximo_uso))

                record.bono_valido = True
                record.inf_bono = [(6,0,[bono.id])]
                record.bono = bono.id

    @api.multi
    def agregar(self):
        self.ensure_one()

        if self.habitacion.ultmovimiento.bono_id:
            raise Warning('Ya se redimió un bono para esta habitación')
        self.habitacion.ultmovimiento.write({'bono_id': self.bono.id})
        self.bono.write({'usos': self.bono.usos + 1})
        return True