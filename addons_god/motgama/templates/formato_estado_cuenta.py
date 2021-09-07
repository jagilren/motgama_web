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

        totales = {}
        for doc in docs:
            recaudos = doc.movimiento.recaudo_ids
            total = doc.amount_total
            for recaudo in recaudos:
                for pago in recaudo.pagos:
                    total -= pago.valor
            total = "{:0,.2f}".format(total).replace(',','¿').replace('.',',').replace('¿','.')
            totales[doc.id] = total
        
        return {
            'docs': docs,
            'impCons': impCons,
            'totales': totales
        }