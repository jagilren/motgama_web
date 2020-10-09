from odoo import fields, models, api
from odoo.exceptions import Warning

from datetime import datetime

class StockAuxReportWizard(models.TransientModel):
    _name = 'stock_aux_report.stock_aux_report_wizard'

    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')
    ubicacion_id = fields.Many2one(comodel_name='stock.location',string='Ubicación')
    producto_ids = fields.Many2many(comodel_name='product.product',string='Productos')

    @api.multi
    def get_report(self):
        self.ensure_one()

        reporte = self.env['stock_aux_report.stock_aux_report'].search([])
        for linea in reporte:
            linea.unlink()

        fecha_inicial = self.fecha_inicial or datetime(2000,1,1)
        fecha_final = self.fecha_final or fields.Datetime().now()
        if self.ubicacion_id:
            ubicaciones = self.env['stock.location'].search('id','child_of',[self.ubicacion_id.id])
        else:
            ubicaciones = self.env['stock.location'].search([('usage','=','internal')])
        if self.producto_ids:
            productos = self.producto_ids
        else:
            productos = self.env['product.product'].search([])
    
        transferencias = self.env['stock.move'].search(['&','&','&','|',('location_id','in',ubicaciones.ids),('location_dest_id','in',ubicaciones.ids),('state','=','done'),('product_id','in',productos.ids),('date','<=',fecha_final)])
        reporte_aux = {}
        for transferencia in transferencias:
            if transferencia.location_id in reporte_aux:
                if transferencia.product_id in reporte_aux[transferencia.location_id]:
                    if transferencia.date < fecha_inicial:
                        if 'initial' in reporte_aux[transferencia.location_id][transferencia.product_id]:
                            reporte_aux[transferencia.location_id][transferencia.product_id]['initial'] -= transferencia.product_qty
                        else:
                            reporte_aux[transferencia.location_id][transferencia.product_id]['initial'] = 0 - transferencia.product_qty
                    else:
                        if 'product_out' in reporte_aux[transferencia.location_id][transferencia.product_id][transferencia.picking_id.partner_id]:
                                reporte_aux[transferencia.location_id][transferencia.product_id]['product_out'] += transferencia.product_qty
                        else:
                            reporte_aux[transferencia.location_id][transferencia.product_id]['product_out'] = transferencia.product_qty
                else:
                    reporte_aux[transferencia.location_id][transferencia.product_id] = {}
                    if transferencia.date < fecha_inicial:
                        reporte_aux[transferencia.location_id][transferencia.product_id]['initial'] = 0 - transferencia.product_qty
                    else:
                        reporte_aux[transferencia.location_id][transferencia.product_id]['product_out'] = transferencia.product_qty
            elif transferencia.location_id in ubicaciones:
                reporte_aux[transferencia.location_id] = {
                    transferencia.product_id: {}
                }
                if transferencia.date < fecha_inicial:
                    reporte_aux[transferencia.location_id][transferencia.product_id]['initial'] = 0 - transferencia.product_qty
                else:
                    reporte_aux[transferencia.location_id][transferencia.product_id]['product_out']: transferencia.product_qty}
            
            if transferencia.location_dest_id in reporte_aux:
                if transferencia.product_id in reporte_aux[transferencia.location_dest_id]:
                    if transferencia.date < fecha_inicial:
                        if 'initial' in reporte_aux[transferencia.location_dest_id][transferencia.product_id]:
                            reporte_aux[transferencia.location_dest_id][transferencia.product_id]['initial'] += transferencia.product_qty
                        else:
                            reporte_aux[transferencia.location_dest_id][transferencia.product_id]['initial'] = transferencia.product_qty
                    else:
                        if 'product_in' in reporte_aux[transferencia.location_dest_id][transferencia.product_id]:
                            reporte_aux[transferencia.location_dest_id][transferencia.product_id]['product_in'] += transferencia.product_qty
                        else:
                            reporte_aux[transferencia.location_dest_id][transferencia.product_id]['product_in'] = transferencia.product_qty
                else:
                    reporte_aux[transferencia.location_dest_id][transferencia.product_id] = {}
                    if transferencia.date < fecha_inicial:
                        reporte_aux[transferencia.location_dest_id][transferencia.product_id]['initial'] = transferencia.product_qty
                    else:
                        reporte_aux[transferencia.location_dest_id][transferencia.product_id]['product_in'] = transferencia.product_qty
            elif transferencia.location_dest_id in ubicaciones:
                reporte_aux[transferencia.location_dest_id] = {
                    transferencia.product_id: {}
                }
                if transferencia.date < fecha_inicial:
                    reporte_aux[transferencia.location_dest_id][transferencia.product_id]['initial'] = transferencia.product_qty
                else:
                    reporte_aux[transferencia.location_dest_id][transferencia.product_id]['product_in'] = transferencia.product_qty

        reporte = []
        for ubicacion in reporte_aux:
            for producto in reporte_aux[ubicacion]:
                initial = reporte_aux[ubicacion][producto]['initial'] if 'initial' in reporte_aux[ubicacion][producto] else 0
                product_in = reporte_aux[ubicacion][producto]['product_in'] if 'product_in' in reporte_aux[ubicacion][producto] else 0
                product_out = reporte_aux[ubicacion][producto]['product_out'] if 'product_out' in reporte_aux[ubicacion][producto] else 0
                total = initial
                dic = {
                    'producto': producto.name,
                    'ubicacion': ubicacion.name,
                    'inicial': initial,
                    'product_in': product_in,
                    'product_out': product_out,
                    'total': total
                }
        
        for linea in reporte:
            nuevo = self.env['stock_aux_report.stock_aux_report'].create(linea)
            if not nuevo:
                raise Warning('Error al generar el reporte')
        
        return {
            'name': 'Reporte auxiliar de inventarios',
            'view_mode': 'tree',
            'view_id': self.env.ref('stock_aux_report.tree_aux_report').id,
            'res_model': 'stock_aux_report.stock_aux_report',
            'type': 'ir.actions.act_window',
            'context':{
                'search_default_groupby_ubicacion':1,
                'search_default_groupby_producto':1
            },
            'target':'main'
        }