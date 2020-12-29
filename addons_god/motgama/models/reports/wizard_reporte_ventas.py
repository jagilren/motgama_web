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

    @api.model
    def check_permiso(self):
        if self.env.ref('motgama.motgama_informe_diariovtas') not in self.env.user.permisos:
            raise Warning('No tiene permitido generar este informe')
        
        return {
            'type': 'ir.actions.act_window',
            'name': "Reporte de ventas",
            'res_model': "motgama.wizard.reporteventas",
            'view_mode': "form",
            'target': "new"
        }

    @api.multi
    def get_report(self):
        self.ensure_one()

        reporte = self.env['motgama.reporteventas'].search([])
        for x in reporte:
            x.unlink()

        if self.tipo_reporte == 'fecha':
            facturas = self.env['account.invoice'].search([('type','in',['out_invoice','out_refund']),('state','in',['open','paid']),('fecha','<=',self.fecha_final),('fecha','>=',self.fecha_inicial)])
        elif self.tipo_reporte == 'documento':
            facturas = self.env['account.invoice'].search([('type','in',['out_invoice','out_refund']),('state','in',['open','paid']),('id','<=',self.doc_final.id),('id','>=',self.doc_inicial.id)])
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
            if self.tipo_reporte == 'fecha':
                valores.update({
                    'fecha_inicial': self.fecha_inicial,
                    'fecha_final': self.fecha_final,
                    'doc_inicial': False,
                    'doc_final': False
                })
            elif self.tipo_reporte == 'documento':
                valores.update({
                    'doc_inicial': self.doc_inicial.name,
                    'doc_final': self.doc_final.name,
                    'fecha_inicial': False,
                    'fecha_final': False
                })
            medios = []
            for pago in factura.recaudo.pagos:
                if pago.mediopago.tipo == 'prenda' and factura.prenda_id and factura.prenda_id.recaudo:
                    for pago1 in factura.prenda_id.recaudo.pagos:
                        if pago1.mediopago not in medios:
                            medios.append(pago1.mediopago)
                elif pago.mediopago.tipo == 'abono' and factura.movimiento_id:
                    for recaudo in factura.movimiento_id.recaudo_ids:
                        if recaudo.estado == 'anulado' or recaudo == factura.recaudo:
                            continue
                        for pago2 in recaudo.pagos:
                            if pago2.mediopago in ['prenda','abono']:
                                continue
                            if pago2.mediopago not in medios:
                                medios.append(pago2.mediopago)
                elif pago.mediopago in medios:
                    continue
                else:
                    medios.append(pago.mediopago)
            if len(medios) == 1:
                valores['medio_pago'] = medios[0].nombre
            else:
                med = ''
                for medio in medios:
                    if med != '':
                        med += '-'
                    cod = medio.cod if medio.cod else medio.nombre[:2].upper()
                    med += cod
                valores['medio_pago'] = med
            if factura.type == 'out_refund':
                valores['medio_pago'] = 'Nota Crédito'
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

    fecha_inicial = fields.Datetime(string="Fecha inicial")
    fecha_final = fields.Datetime(string="Fecha final")
    doc_inicial = fields.Char(string='Factura inicial')
    doc_final = fields.Char(string='Factura final')

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
        imps = {}
        for doc in docs:
            total += doc.valor

            for linea in doc.factura.invoice_line_ids:
                if linea.product_id.categ_id in prods:
                    prods[linea.product_id.categ_id] += linea.price_unit * linea.quantity
                else:
                    prods[linea.product_id.categ_id] = linea.price_unit * linea.quantity

            for pago in doc.factura.recaudo.pagos:
                if pago.mediopago.tipo == 'prenda' and doc.factura.prenda_id and doc.factura.prenda_id.recaudo:
                    for pago1 in doc.factura.prenda_id.recaudo.pagos:
                        if pago1.mediopago in medios:
                            medios[pago1.mediopago] += pago1.valor
                        else:
                            medios[pago1.mediopago] = pago1.valor
                elif pago.mediopago.tipo == 'abono' and doc.factura.movimiento_id:
                    for recaudo in doc.factura.movimiento_id.recaudo_ids:
                        if recaudo.estado == 'anulado' or recaudo == doc.factura.recaudo:
                            continue
                        for pago2 in recaudo.pagos:
                            if pago2.mediopago in ['prenda','abono']:
                                continue
                            if pago2.mediopago in medios:
                                medios[pago2.mediopago] += pago2.valor
                            else:
                                medios[pago2.mediopago] = pago2.valor
                elif pago.mediopago in medios:
                    medios[pago.mediopago] += pago.valor
                else:
                    medios[pago.mediopago] = pago.valor
            
            for linea_impuesto in doc.factura.tax_line_ids:
                if linea_impuesto.tax_id in imps:
                    imps[linea_impuesto.tax_id] += linea_impuesto.amount_total
                else:
                    imps[linea_impuesto.tax_id] = linea_impuesto.amount_total

        for prod in prods:
            prods[prod] = "$ {:0,.2f}".format(prods[prod]).replace(',','¿').replace('.',',').replace('¿','.')
        for medio in medios:
            medios[medio] = "$ {:0,.2f}".format(medios[medio]).replace(',','¿').replace('.',',').replace('¿','.')
        for imp in imps:
            imps[imp] = "$ {:0,.2f}".format(imps[imp]).replace(',','¿').replace('.',',').replace('¿','.')

        return {
            'company': self.env['res.company']._company_default_get('account.invoice'),
            'sucursal': self.env['motgama.sucursal'].search([],limit=1),
            'docs': docs,
            'count': len(docs),
            'total': "{:0,.2f}".format(total).replace(',','¿').replace('.',',').replace('¿','.'),
            'prods': prods,
            'medios': medios,
            'fecha_inicial': docs[0].fecha_inicial,
            'fecha_final': docs[0].fecha_final,
            'doc_inicial': docs[0].doc_inicial,
            'doc_final': docs[0].doc_final,
            'imps': imps
        }