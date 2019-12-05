from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaConfirmPrestados(models.TransientModel):
    _name = 'motgama.confirm.prestados'
    _description = 'Mensaje de confirmación al liquidar o recaudar si existen objetos prestados'

    texto = fields.Text(string="",compute="_compute_texto")
    habitacion = fields.Many2one(comodel_name="motgama.flujohabitacion", default=lambda self: self._get_habitacion())

    @api.model
    def _get_habitacion(self):
        habitacion = self.env.context['active_id']
        if self.env['motgama.flujohabitacion'].search([('id','=',habitacion)],limit=1):
            return habitacion
        else:
            raise Warning('Error del sistema')

    @api.depends('habitacion')
    def _compute_texto(self):
        for record in self:
            if record.habitacion:
                if record.habitacion.estado in ['OO','OA']:
                    record.texto = "Existen actualmente objetos prestados en la habitacion ¿Está seguro que desea liquidar?"
                elif record.habitacion.estado == 'LQ':
                    record.texto = "Existen actualmente objetos prestados en la habitacion ¿Está seguro que desea recaudar?"

    @api.multi
    def confirmar(self):
        self.ensure_one()
        if self.habitacion.estado in ['OO','OA']:
            self.habitacion.write({'puede_liquidar': True})
            self.habitacion.button_liquidar()
        if self.habitacion.estado == 'LQ':
            self.habitacion.write({'puede_recaudar': True})
            return self.habitacion.button_recaudar()
        
        return True
