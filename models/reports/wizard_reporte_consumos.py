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
                consumos = self.env['motgama.consumo'].search([('active','=',True)])
            else:
                consumos = self.env['motgama.consumo'].search([('recepcion','=',recepcion.id),('active','=',True)])
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
                consumos = self.env['motgama.consumo'].search(['|',('active','=',False),('active','=',True)])
            else:
                consumos = self.env['motgama.consumo'].search(['&',('recepcion','=',recepcion.id),'|',('active','=',True),('active','=',False)])
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
                'recepcion': consumo.lugar_id.recepcion.nombre,
                'fecha': consumo.create_date,
                'habitacion': consumo.habitacion.codigo,
                'producto': consumo.producto_id.name,
                'cantidad': consumo.cantidad,
                'valorUnitario': consumo.vlrUnitario,
                'valorTotal': consumo.vlrSubtotal,
                'usuario': consumo.create_uid.name,
                'categoria': consumo.producto_id.categ_id.name
            }
            nuevo = self.env['motgama.reporteconsumos'].create(valores)
            if not nuevo:
                raise Warning('No se pudo crear el reporte')
        
        if self.tipo_reporte == 'fecha':
            ids = []
            lineas = self.env['motgama.lineafacturaconsumos'].search([('create_date','<',fecha_final),('create_date','>',fecha_inicial)])
            for linea in lineas:
                if not recepcion:
                    ids.append(linea)
                else:
                    if linea.create_uid.recepcion_id.id == recepcion.id:
                        ids.append(linea)
            for consumo in ids:
                valores = {
                    'recepcion': consumo.factura_id.recepcion.nombre,
                    'fecha': consumo.create_date,
                    'producto': consumo.producto_id.name,
                    'cantidad': consumo.cantidad,
                    'valorUnitario': consumo.vlrUnitario,
                    'valorTotal': consumo.vlrSubtotal,
                    'usuario': consumo.create_uid.name,
                    'categoria': consumo.producto_id.categ_id.name
                }
                nuevo = self.env['motgama.reporteconsumos'].create(valores)
                if not nuevo:
                    raise Warning('No se pudo crear el reporte')

        return {
            'name': 'Reporte de consumos',
            'view_mode': 'tree',
            'view_id': self.env.ref('motgama.tree_reporte_consumo').id,
            'res_model': 'motgama.reporteconsumos',
            'type': 'ir.actions.act_window',
            'context':{
                'search_default_groupby_categoria':1,
                'search_default_groupby_producto':1
            },
            'target':'main'
        }


class ReporteConsumos(models.TransientModel):
    _name = 'motgama.reporteconsumos'

    recepcion = fields.Char(string='Recepción')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Char(string='Habitación')
    producto = fields.Char(string='Producto')
    cantidad = fields.Float(string='Cantidad')
    valorUnitario = fields.Float(string='Valor Unitario')
    valorTotal = fields.Float(string='Valor Total')
    usuario = fields.Char(string='Usuario')

    # Campos no visibles
    categoria = fields.Char(string='Categoría')

