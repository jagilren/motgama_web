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
                consumos = self.env['motgama.consumo'].sudo().search([('active','=',True)])
            else:
                consumos = self.env['motgama.consumo'].sudo().search([('recepcion','=',recepcion.id),('active','=',True)])
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
                consumos = self.env['motgama.consumo'].sudo().search(['|',('active','=',False),('active','=',True)])
            else:
                consumos = self.env['motgama.consumo'].sudo().search(['&',('recepcion','=',recepcion.id),'|',('active','=',True),('active','=',False)])
            if not consumos:
                raise Warning('No hay consumos qué mostrar')

            for consumo in consumos:
                if fecha_inicial < consumo.create_date < fecha_final:
                    ids.append(consumo)

        else:
            raise Warning('Seleccione un tipo de reporte')

        consumos = self.env['motgama.reporteconsumos'].sudo().search([])
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
            nuevo = self.env['motgama.reporteconsumos'].sudo().create(valores)
            if not nuevo:
                raise Warning('No se pudo crear el reporte')
        
        if self.tipo_reporte == 'fecha':
            ids = []
            lineas = self.env['motgama.lineafacturaconsumos'].sudo().search([('create_date','<',fecha_final),('create_date','>',fecha_inicial)])
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
                nuevo = self.env['motgama.reporteconsumos'].sudo().create(valores)
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

class PDFReporteConsumos(models.AbstractModel):
    _name = 'report.motgama.reporteconsumos'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reporteconsumos'].sudo().browse(docids)

        productos = {}
        categorias = {}
        totalconsumos = 0
        for doc in docs:
            if doc.producto in productos:
                valores = {
                    'cantidad': productos[doc.producto]['cantidad'] + doc.cantidad,
                    'valor': productos[doc.producto]['valor'] + doc.valorTotal
                }
            else:
                valores = {
                    'cantidad': doc.cantidad,
                    'valor': doc.valorTotal
                }
            productos[doc.producto] = valores
            
            if doc.categoria in categorias:
                total = categorias[doc.categoria] + doc.valorTotal
            else:
                total = doc.valorTotal
            categorias[doc.categoria] = total

            totalconsumos += doc.valorTotal
        
        for prod in productos:
            productos[prod]['valor'] = "{:0,.1f}".format(productos[prod]['valor']).replace(',','¿').replace('.',',').replace('¿','.')
        for categ in categorias:
            categorias[categ] = "{:0,.1f}".format(categorias[categ]).replace(',','¿').replace('.',',').replace('¿','.')
            
        return {
            'docs': docs,
            'productos': productos,
            'categorias': categorias,
            'total': "{:0,.1f}".format(totalconsumos).replace(',','¿').replace('.',',').replace('¿','.')
        }