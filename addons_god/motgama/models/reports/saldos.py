from odoo import models, fields, api

class ReporteSaldos(models.AbstractModel):
    _name = 'report.motgama.reportesaldoshoy'
    _description = 'Reporte de saldos a la fecha'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.quant'].browse(docids)

        return {
            'docs': docs,
            'sucursal': self.env['motgama.sucursal'].search([],limit=1).nombre
        }

class ReporteSaldos(models.AbstractModel):
    _name = 'report.motgama.reportesaldosfecha'
    _description = 'Reporte de saldos a la fecha'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['product.product'].browse(docids)

        return {
            'docs': docs,
            'sucursal': self.env['motgama.sucursal'].search([],limit=1).nombre
        }

class Product(models.Model):
    _inherit = 'product.product'

    fecha_reporte = fields.Datetime(string="Fecha de reporte")

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    fecha_reporte = fields.Datetime(string="Fecha de reporte")

class StockQuantHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    @api.multi
    def open_table(self):
        self.ensure_one

        if self.compute_at_date:
            action = super().open_table()
            prods = self.env['product.product'].search([])
            for prod in prods:
                prod.write({'fecha_reporte': self.date})
            return action
        else:
            action = super().open_table()
            quants = self.env['stock.quant'].search([])
            for quant in quants:
                quant.sudo().write({'fecha_reporte': fields.Datetime().now()})
            return action