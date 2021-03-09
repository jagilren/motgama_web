from odoo import models, fields, api

class StockAuxReport(models.TransientModel):
    _name = 'stock_aux_report.stock_aux_report'
    _order = 'id asc'
    _rec_name = 'producto'

    currency_id = fields.Many2one(string='Moneda',comodel_name='res.currency',default=lambda self: self._get_currency())

    fecha_inicial = fields.Datetime(string="Fecha inicial")
    fecha_final = fields.Datetime(string="Fecha final")
    genera_uid = fields.Many2one(string="Usuario que genera",comodel_name="res.users")
    
    ubicacion = fields.Char(string='Ubicación')
    categoria = fields.Char(string='Categoría')
    producto = fields.Char(string='Producto')
    inicial = fields.Float(string='Saldo anterior')
    valor_ant = fields.Monetary(string='Valor anterior')
    product_in = fields.Float(string='Entradas')
    product_out = fields.Float(string='Salidas')
    total = fields.Float(string='Saldo actual')
    valor_act = fields.Monetary(string='Valor actual')

    move_ids = fields.Many2many(string='Movimientos de inventario',comodel_name='stock.move')

    @api.model
    def _get_currency(self):
        return self.env['res.company']._company_default_get('account.invoice').currency_id.id

class ReportStockAuxComplete(models.AbstractModel):
    _name = 'report.stock_aux_report.stock_aux_report_complete_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock_aux_report.stock_aux_report'].search([])
        if not docs:
            raise Warning('Error al imprimir, los datos no existen, vuelva a generar el reporte')
        
        rep = {}
        for doc in docs:
            if doc.categoria in rep:
                rep[doc.categoria].append(doc)
            else:
                rep[doc.categoria] = [doc]
        
        return {
            'docs': rep,
            'sucursal': self.env['motgama.sucursal'].search([],limit=1).nombre
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
            if doc.categoria in rep:
                rep[doc.categoria].append(doc)
            else:
                rep[doc.categoria] = [doc]
        
        return {
            'docs': rep,
            'sucursal': self.env['motgama.sucursal'].search([],limit=1).nombre
        }