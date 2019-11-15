from odoo import models, fields, api
from odoo.exceptions import Warning

class WizardReporteConsumos(models.TransientModel):
    _name = 'motgama.wizard.reporteconsumo'

    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')

    @api.multi
    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'habitacion': self.habitacion.id
            }
        }

        return self.env.ref('motgama.reporte_consumo').report_action(self,data=data)

class ReporteConsumos(models.AbstractModel):
    _name = 'report.motgama.reporteconsumos'

    @api.model
    def _get_report_values(self,docids,data=None):
        idHabitacion = data['form']['habitacion']

        docs = []
        habitacion = self.env['motgama.flujohabitacion'].search([('id','=',idHabitacion)])
        if not habitacion:
            raise Warning('No existe la habitación')
        if habitacion.estado != 'OO' and habitacion.estado != 'OA' and habitacion.estado != 'LQ':
            raise Warning('La habitación no está ocupada')
        movimiento = habitacion.ultmovimiento.id

        consumos = self.env['motgama.consumo'].search([('movimiento_id','=',movimiento)])
        if not consumos:
            raise Warning('La habitación no tiene consumos')
        for consumo in consumos:
            docs.append({
                 'producto': consumo.producto_id.name,
                 'cantidad': consumo.cantidad,
                 'vlrTotal': consumo.vlrSubtotal
            })
        
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'habitacion': habitacion.codigo,
            'docs': docs
        }
