from odoo import models, fields, api
from odoo.exceptions import Warning

class WizardReporteConsumos(models.TransientModel):
    _name = 'motgama.wizard.reporteconsumo'

    tipo_reporte = fields.Selection(string='Tipo de reporte', selection=[('transito','En tránsito'),('fecha','En una fecha específica')], default='transito')
    fecha_inicial = fields.Datetime(string='Fecha Inicial')
    fecha_final = fields.Datetime(string='Fecha final')
    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')

    @api.multi
    def get_report(self):
        self.ensure_one()

        if self.tipo_reporte == 'transito':
            recepcion = self.recepcion
            ids = []
            if not recepcion:
                consumos = self.env['motgama.consumo'].search([])
            else:
                consumos = self.env['motgama.consumo'].search([('recepcion','=',recepcion.id)])
            if not consumos:
                raise Warning('No hay consumos qué mostrar')
            for consumo in consumos:
                if consumo.habitacion.estado == 'OO' or consumo.habitacion.estado == 'OA' or consumo.habitacion.estado == 'LQ':
                    ids.append(consumo)
        
        elif self.tipo_reporte == 'fecha':
            fecha_inicial = self.fecha_inicial
            fecha_final = self.fecha_final
            if fecha_inicial > fecha_final:
                raise Warning('La fecha final debe ser después de la fecha inicial')

            recepcion = self.recepcion
            ids = []
            if not recepcion:
                consumos = self.env['motgama.consumo'].search([])
            else:
                consumos = self.env['motgama.consumo'].search([('recepcion','=',recepcion.id)])
            if not consumos:
                raise Warning('No hay consumos qué mostrar')

            for consumo in consumos:
                if fecha_inicial < consumo.create_date < fecha_final:
                    ids.append(consumo)

        else:
            raise Warning('Seleccione un tipo de reporte')

        consumos = self.env['motgama.reporteconsumos'].search([])
        if consumos:
            for consumo in consumos:
                consumo.unlink()

        for consumo in ids:
            valores = {
                'recepcion': consumo.recepcion.id,
                'fecha': consumo.create_date,
                'habitacion': consumo.habitacion.id,
                'producto': consumo.producto_id.id,
                'cantidad': consumo.cantidad,
                'valorUnitario': consumo.vlrUnitario,
                'valorTotal': consumo.vlrSubtotal,
                'usuario': consumo.create_uid.id,
                'categoria': consumo.producto_id.categ_id.id
            }
            nuevo = self.env['motgama.reporteconsumos'].create(valores)
            if not nuevo:
                raise Warning('No se pudo crear el reporte')
        
        return {
            'name': 'Reporte de consumos',
            'view_mode': 'tree',
            'view_id': self.env.ref('motgama.tree_reporte_consumo').id,
            'res_model': 'motgama.reporteconsumos',
            'type': 'ir.actions.act_window'
        }


class ReporteConsumos(models.TransientModel):
    _name = 'motgama.reporteconsumos'

    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion')
    producto = fields.Many2one(string='Producto',comodel_name='product.template')
    cantidad = fields.Float(string='Cantidad')
    valorUnitario = fields.Float(string='Valor Unitario')
    valorTotal = fields.Float(string='Valor Total')
    usuario = fields.Many2one(string='Usuario',comodel_name='res.users')

    # Campos no visibles
    categoria = fields.Many2one(string='Categoría', comodel_name="product.category")

class ReporteConsumosAbstracto(models.AbstractModel):
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
