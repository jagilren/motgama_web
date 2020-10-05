from odoo import models, fields, api

from datetime import datetime

class StockAuxView(models.TransientModel):
    _name = 'stock.aux.view'
    _description = 'Stock Aux View'
    _order = 'fecha'

    fecha = fields.Datetime()
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

    fecha_inicial = fields.Datetime()
    fecha_final = fields.Datetime()
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
        
        self.env['stock.move']
        self._cr.execute("""
            SELECT move.date, move.product_id, move.product_qty,
                move.product_uom_qty, move.product_uom, move.reference,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                case when move.date < %s then True else False end as is_initial
            FROM stock_move move
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) <= %s
            ORDER BY move.date, move.reference
        """, (
            tuple(ubicaciones.ids), tuple(ubicaciones.ids), fecha_inicial,
            tuple(ubicaciones.ids), tuple(ubicaciones.ids),
            tuple(productos.ids), fecha_final))