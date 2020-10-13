from odoo import models, fields, api

class StockAuxReport(models.TransientModel):
    _name = 'stock_aux_report.stock_aux_report'
    _order = 'id asc'

    categoria = fields.Char(string='Categoría')
    producto = fields.Char(string='Producto')
    ubicacion = fields.Char(string='Ubicación')
    inicial = fields.Float(string='Cantidad inicial')
    product_in = fields.Float(string='Cantidad que ingresa')
    product_out = fields.Float(string='Cantidad que sale')
    total = fields.Float(string='Cantidad total')

    move_ids = fields.Many2many(string='Movimientos de inventario',comodel_name='stock.move')

class ReportStockAuxComplete(models.AbstractModel):
    _name = 'report.stock_aux_report.stock_aux_report_complete_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock_aux_report.stock_aux_report'].search([])
        if not docs:
            raise Warning('Error al imprimir, los datos no existen, vuelva a generar el reporte')
        
        rep = {}
        for doc in docs:
            if doc.ubicacion in rep:
                if doc.categoria in rep[doc.ubicacion]:
                    rep[doc.ubicacion][doc.categoria].append(doc)
                else:
                    rep[doc.ubicacion][doc.categoria] = [doc]
            else:
                rep[doc.ubicacion] = {doc.categoria: [doc]}
        
        return {
            'docs': rep
        }

class ReportStockAux(models.AbstractModel):
    _name = 'report.stock_aux_report.stock_aux_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock_aux_report.stock_aux_report'].browse(docids)
        if not docs:
            raise Warning('No se puede imprimir el reporte: No seleccionó ningún registro')

        rep = {}
        for doc in docs:
            if doc.ubicacion in rep:
                if doc.categoria in rep[doc.ubicacion]:
                    rep[doc.ubicacion][doc.categoria].append(doc)
                else:
                    rep[doc.ubicacion][doc.categoria] = [doc]
            else:
                rep[doc.ubicacion] = {doc.categoria: [doc]}
        
        return {
            'docs': rep
        }