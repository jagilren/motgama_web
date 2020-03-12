from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardPlaca(models.TransientModel):
    _name = 'motgama.wizard.placa'
    _sql_constraints = [('placa_uniq','unique (placa)',"La placa ya Existe, Verifique!")]

    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento',default=lambda self: self._get_movimiento())
    placa = fields.Char(string='Placa del Vehiculo',placeholder='AAA111',default=lambda self: self._get_placa()) 
    descripcion = fields.Text(string='Descripción del evento',required=True)
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular','Particular'),('moto','Moto'),('taxi','Taxi')],default=lambda self: self._get_tipo())    
    tiporeporte = fields.Selection(string='Tipo de reporte',selection=[('positivo','Positivo'),('negativo','Negativo')],default='positivo',required=True)
    vinculo = fields.Char(string='Vínculo del vehículo')

    @api.model
    def _get_movimiento(self):
        habitacion = self.env.context['active_id']
        obj = self.env['motgama.flujohabitacion'].search([('id','=',habitacion)],limit=1)
        return obj.ultmovimiento.id

    @api.model
    def _get_placa(self):
        habitacion = self.env.context['active_id']
        obj = self.env['motgama.flujohabitacion'].search([('id','=',habitacion)],limit=1)
        return obj.ultmovimiento.placa_vehiculo

    @api.model
    def _get_tipo(self):
        habitacion = self.env.context['active_id']
        obj = self.env['motgama.flujohabitacion'].search([('id','=',habitacion)],limit=1)
        return obj.ultmovimiento.tipovehiculo

    @api.multi
    def reportar(self):
        self.ensure_one()

        valores = {
            'placa': self.placa,
            'descripcion': self.descripcion,
            'tipovehiculo': self.tipovehiculo,
            'tiporeporte': self.tiporeporte,
            'vinculo': self.vinculo
        }
        placa = self.env['motgama.placa'].create(valores)
        if not placa:
            raise Warning('No se pudo registrar el evento de placa')

        return True

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    @api.multi
    def button_reporte_placa(self):
        self.ensure_one()

        if not self.ultmovimiento.placa_vehiculo:
            raise Warning('No se registró placa de vehículo, puede hacer el reporte en el menú Procesos -> Placas Registradas')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.placa',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_placa_form').id,
            'target': 'new',
            'name': 'Reportar placa ' + self.ultmovimiento.placa_vehiculo
        }