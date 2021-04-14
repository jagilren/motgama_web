from odoo import models, fields, api

class PDFEstadoCuenta(models.AbstractModel):
    _name = 'report.motgama.formato_estadocuenta'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['sale.order'].sudo().browse(docids)

        paramImpCons = self.env['motgama.parametros'].search([('codigo','=','IMPCONSCTACOBRO')], limit=1)
        if paramImpCons:
            if paramImpCons.valor == 's' or paramImpCons == 'S':
                impCons = True
            else:
                impCons = False
        else:
            impCons = False
        
        return {
            'docs': docs,
            'impCons': impCons
        }