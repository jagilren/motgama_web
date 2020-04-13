from odoo import fields, models, api
from odoo.exceptions import Warning

class WizardReporteVentas(models.TransientModel):
    _name = 'motgama.wizard.reporteventas'
    _description = 'Wizard del Reporte de Ventas'

    tipo_reporte = fields.Selection(string='Tipo de reporte',selection=[('fecha','Por fecha'),('documento','Por factura')],default='fecha')

    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')

    doc_inicial = fields.Many2one(string='Factura inicial',comodel_name='account.invoice')
    doc_final = fields.Many2one(string='Factura final',comodel_name='account.invoice')

    es_manual = fields.Boolean(string='Es manual',default=True)

    @api.multi
    def get_report(self):
        self.ensure_one()

        if self.tipo_reporte == 'fecha':
            facturas = self.env['account.invoice'].search([('state','in',['open','paid']),('fecha','<=',self.fecha_final),('fecha','>=',self.fecha_inicial)])
        elif self.tipo_reporte == 'documento':
            facturas = self.env['account.invoice'].search([('state','in',['open','paid']),('id','<=',self.doc_final.id),('id','>=',self.doc_inicial.id)])
        else:
            facturas = []
        if not facturas:
            raise Warning('No hay datos que mostrar')

        for factura in facturas:
            valores = {
                'factura': factura.id,
                'fecha': factura.fecha,
                'fac': factura.number,
                'cliente': factura.partner_id.name,
                'habitacion': factura.habitacion_id.codigo or '',
                'valor': factura.amount_total,
                'usuario': factura.user_id.name
            }
            medios = []
            for pago in factura.recaudo.pagos:
                if pago.mediopago in medios:
                    continue
                else:
                    medios.append(pago.mediopago)
            if len(medios) == 1:
                valores['medio_pago'] = medios[0].nombre
            else:
                valores['medio_pago'] = 'Múltiple'
            nuevo = self.env['motgama.reporteventas'].create(valores)
            if not nuevo:
                raise Warning('No fue posible generar el reporte')
        
        if self.es_manual:
            return {
                'name': 'Reporte de ventas',
                'view_mode':'tree',
                'view_id': self.env.ref('motgama.tree_reporte_ventas').id,
                'res_model': 'motgama.reporteventas',
                'type': 'ir.actions.act_window',
                'target': 'main'
            }
        else:
            return True

class MotgamaReporteVentas(models.TransientModel):
    _name = 'motgama.reporteventas'
    _description = 'Reporte de Ventas'

    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')

    fecha = fields.Datetime(string='Fecha')
    fac = fields.Char(string='Factura')
    cliente = fields.Char(string='Cliente')
    habitacion = fields.Char(string='Habitación')
    valor = fields.Float(string='Valor Total')
    medio_pago = fields.Char(string='Medio de pago')
    usuario = fields.Char(string='Usuario')

class PDFReporteVentas(models.AbstractModel):
    _name = 'report.motgama.reporteventas'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reporteventas'].browse(docids)

        total = 0
        prods = {}
        medios = {}
        for doc in docs:
            total += doc.valor

            for linea in doc.factura.invoice_line_ids:
                if linea.product_id.categ_id in prods:
                    prods[linea.product_id.categ_id] += linea.price_unit * linea.quantity
                else:
                    prods[linea.product_id.categ_id] = linea.price_unit * linea.quantity

            for pago in doc.factura.recaudo.pagos:
                if pago.mediopago in medios:
                    medios[pago.mediopago] += pago.valor
                else:
                    medios[pago.mediopago] = pago.valor
        
        for prod in prods:
            prods[prod] = "$ {:0,.2f}".format(prods[prod]).replace(',','¿').replace('.',',').replace('¿','.')
        for medio in medios:
            medios[medio] = "$ {:0,.2f}".format(medios[medio]).replace(',','¿').replace('.',',').replace('¿','.')

        return {
            'docs': docs,
            'count': len(docs),
            'total': "$ {:0,.2f}".format(total).replace(',','¿').replace('.',',').replace('¿','.'),
            'prods': prods,
            'medios': medios
        }