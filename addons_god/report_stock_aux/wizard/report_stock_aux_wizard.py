from odoo import models, fields, api
from odoo.tools import pycompat
from odoo.tools.safe_eval import safe_eval

class StockReportAuxWizard(models.TransientModel):
    _name = 'stock.aux.report.wizard'
    _description = 'Reporte Auxiliar de Inventario'

    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')

    ubicacion_id = fields.Many2one(comodel_name='stock.location',string='Ubicación')
    producto_ids = fields.Many2many(comodel_name='product.product',string='Productos')

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref('report_stock_aux.action_report_report_stock_aux_html')
        vals = action.read()[0]
        context = vals.get('context',{})
        if isinstance(context, pycompat.string_types):
            context = safe_eval(context)
        model = self.env['report.report.stock.aux']
        report = model.create(self._prepare_report_stock_aux())
        context['active_id'] = report.id
        context['active_ids'] = report.ids
        vals['context'] = context

        return vals
    
    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)
    
    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_report_stock_aux(self):
        self.ensure_one()
        return {
            'fecha_inicial': self.fecha_inicial,
            'fecha_final': self.fecha_final,
            'producto_ids': self.producto_ids,
            'ubicacion_id': self.ubicacion_id,
        }
    
    def _export(self, report_type):
        model = self.env['report.report.stock.aux']
        report = model.create(self._prepare_report_stock_aux())
        return report.print_report(report_type)