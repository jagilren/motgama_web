from odoo import fields, models, api
from datetime import date

class StockAuxReportWizard(models.TransientModel):
    _name = 'stock_aux_report.stock_aux_report_wizard'

    fecha_inicial = fields.Date(string='Fecha inicial')
    fecha_final = fields.Date(string='Fecha final')
    ubicacion_id = fields.Many2one(comodel_name='stock.location',string='Ubicación')
    producto_ids = fields.Many2many(comodel_name='product.product',string='Productos')

    @api.multi
    def get_report(self):
        self.ensure_one()

        fecha_inicial = self.fecha_inicial or date(2000,1,1)
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
        reporte_aux = []
        for transferencia in transferencias:
            valores = {
                'product_id': transferencia.product_id.id,
                'location_id': transferencia.location_id.id,
                'location_dest_id': transferencia.location_dest_id.id
            }
            if transferencia.location_dest_id.id in ubicaciones.ids:
                valores['product_in']: transferencia.product_qty
                valores['product_out']: 0
            if transferencia.location_id.id in ubicaciones.ids:
                valores['product_out']: transferencia.product_qty
                valores['product_in']: 0
            valores['is_initial']: bool(transferencia.date < fecha_inicial)
            reporte_card.append(valores)

        reporte_ubicaciones = {}
        for movimiento in reporte_card: