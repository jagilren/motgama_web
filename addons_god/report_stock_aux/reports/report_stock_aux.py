from odoo import models, fields, api

from datetime import datetime

class StockAuxView(models.TransientModel):
    _name = 'stock.aux.view'
    _description = 'Stock Aux View'
    _order = 'fecha'

    fecha = fields.Date()
    product_id = fields.Many2one(comodel_name='product.product')
    product_qty = fields.Float()
    product_uom_qty = fields.Float
    product_uom = fields.Many2one(comodel_name='uom.uom')
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name='stock.location')
    location_dest_id = fields.Many2one(comodel_name='stock.location')
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()

class ReportStockAux(models.TransientModel):
    _name = 'report.report.stock.aux'
    _description = 'Reporte Auxiliar de Inventario'

    fecha_inicial = fields.Date()
    fecha_final = fields.Date()
    producto_ids = fields.Many2many(comodel_name='product.product')
    ubicacion_id = fields.Many2one(comodel_name='stock.location')

    resultados = fields.Many2many(comodel_name='stock.aux.view',compute='_compute_resultados')

    @api.multi
    def _compute_resultados(self):
        self.ensure_one()
        fecha_inicial = self.fecha_inicial or datetime(2000,0,1)
        fecha_final = self.fecha_final or fields.Datetime().now()
        if self.ubicacion_id:
            ubicaciones = self.env['stock.location'].search('id','child_of',[self.ubicacion_id.id])
        else:
            ubicaciones = self.env['stock.location'].browse()
        if self.producto_ids:
            productos = self.producto_ids
        else:
            productos = self.env['product.product'].browse()
        
        transferencias = self.env['stock.move'].search(['&','&','&','|',('location_id','in',ubicaciones.ids),('location_dest_id','in',ubicaciones.ids),('state','=','done'),('product_id','in',productos.ids),('date','<=',fecha_final)])
        transferencias = transferencias.sorted(key=lambda p: (p.date, p.reference))
        reporte_card = []
        for transferencia in transferencias:
            valores = {
                'fecha': transferencia.date,
                'product_id': transferencia.product_id.id,
                'product_qty': transferencia.product_qty,
                'product_uom_qty': transferencia.product_uom_qty,
                'product_uom': transferencia.product_uom.id,
                'reference': transferencia.reference,
                'location_id': transferencia.location_id.id,
                'location_dest_id': transferencia.location_dest_id.id
            }
            if transferencia.location_dest_id.id in ubicaciones.ids:
                valores['product_in']: transferencia.product_qty
            if transferencia.location_id.id in ubicaciones.ids:
                valores['product_out']: transferencia.product_qty
            valores['is_initial']: bool(transferencia.date < fecha_inicial)
            reporte_card.append(valores)
        reporte_ubicaciones = {}
        for movimiento in reporte_card:
            if movimiento['location_id'] in reporte_ubicaciones and movimiento['location_id'] in ubicaciones.ids:
                if movimiento['product_id'] in reporte_ubicaciones[movimiento['location_id']]:
                    reporte_ubicaciones[movimiento['location_id']][movimiento['product_id']]['product_out'] += movimiento['product_qty']
                else:
                    reporte_ubicaciones[movimiento['location_id']][movimiento['product_id']] = {
                        'product_id': movimiento['product_id'],
                        'product_out': movimiento['product_qty'],
                        'location_id': movimiento['location_id']
                    }
            elif movimiento['location_dest_id'] in reporte_ubicaciones and movimiento['location_dest_id'] in ubicaciones.ids:
                if movimiento['product_id'] in reporte_ubicaciones[movimiento['location_dest_id']]:
                    reporte_ubicaciones[movimiento['location_dest_id']][movimiento['product_id']]['product_in'] += movimiento['product_qty']
                else:
                    reporte_ubicaciones[movimiento['location_dest_id']][movimiento['product_id']] = {
                        'product_id': movimiento['product_id'],
                        'product_in': movimiento['product_qty'],
                        'location_id': movimiento['location_dest_id']
                    }
        reporte = []
        for ubicacion in reporte_ubicaciones:
            for producto in reporte_ubicaciones[ubicacion]:
                reporte.append(reporte_ubicaciones[ubicacion][producto])
        ReportLine = self.env['stock.aux.view']
        self.resultados = [ReportLine.new(line).id for line in reporte]

    @api.multi
    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped('product_in'))
        product_output_qty = sum(product_line.mapped('product_out'))
        return product_input_qty - product_output_qty

    @api.multi
    def print_report(self,report_type='qweb'):
        self.ensure_one()
        action = report_type == 'xlsx' and self.env.ref('report_stock_aux.action_report_stock_aux_xlsx') or self.env.ref('report_stock_aux.action_report_stock_aux_pdf')
        return action.report_action(self, config=False)
    
    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref('report_stock_aux.report_report_stock_aux_html').render(rcontext)
        return result

    @api.model
    def get_html(self,given_context=None):
        return self.with_context(given_context)._get_html()