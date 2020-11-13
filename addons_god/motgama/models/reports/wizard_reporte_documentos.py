from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardReporteDocumentos(models.TransientModel):
    _name = 'motgama.wizard.reportedocumentos'
    _description = 'Wizard Reporte Documentos'

    tipo_reporte = fields.Selection(string='Tipo de reporte',selection=[('fecha','Por rango de fechas'),('documento','Por rango de documentos')],default='fecha')
    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')
    doc_inicial = fields.Many2one(string='Documento inicial',comodel_name='sale.order')
    doc_final = fields.Many2one(string='Documento final',comodel_name='sale.order')

    @api.multi
    def get_report(self):
        self.ensure_one()

        if self.tipo_reporte == 'fecha':
            docs = self.env['sale.order'].sudo().search(['|','&',('movimiento','!=',False),'&',('liquidafecha','!=',False),'&',('liquidafecha','>',self.fecha_inicial),('liquidafecha','<',self.fecha_final),'&',('create_date','<',self.fecha_final),('create_date','>',self.fecha_inicial)])
        elif self.tipo_reporte == 'documento':
            id_inicial = self.doc_inicial.id
            id_final = self.doc_final.id
            docs = self.env['sale.order'].sudo().search([('id','<=',id_final),('id','>=',id_inicial)])
        else:
            raise Warning('Seleccione un tipo de reporte')
        if not docs:
            raise Warning('No hay documentos que mostrar')

        reporte = self.env['motgama.reportedocumentos'].sudo().search([])
        for doc in reporte:
            doc.unlink()
        
        for doc in docs:
            valores = {
                'fecha': doc.create_date,
                'doc': doc.name,
                'cliente': doc.partner_id.name,
                'usuario': doc.write_uid.name
            }

            if doc.movimiento and doc.movimiento.liquidafecha:
                valores.update({'habitacion':doc.movimiento.habitacion_id.codigo,'fecha':doc.movimiento.liquidafecha})
            elif doc.movimiento:
                continue
            
            if doc.state == 'cancel':
                valores.update({'estado':'cancelado'})
            elif doc.state == 'sale':
                if doc.invoice_count == 0:
                    valores.update({'estado':'pendiente'})
                else:
                    valores.update({'estado':'facturado'})
            else:
                continue

            if valores['estado'] == 'facturado':
                valores.update({'valor':doc.amount_total})
            else:
                valores.update({'valor':0})
            
            nuevo = self.env['motgama.reportedocumentos'].sudo().create(valores)
            if not nuevo:
                raise Warning('No fue posible generar el informe')
        
        return{
            'name': 'Reporte de Documentos',
            'view_mode':'tree',
            'view_id': self.env.ref('motgama.tree_reporte_documentos').id,
            'res_model': 'motgama.reportedocumentos',
            'type': 'ir.actions.act_window',
            'target': 'main'
        } 

class MotgamaReporteDocumentos(models.TransientModel):
    _name = 'motgama.reportedocumentos'
    _description = 'Reporte de documentos'

    fecha = fields.Datetime(string='Fecha')
    doc = fields.Char(string='Documento')
    cliente = fields.Char(string='Cliente')
    habitacion = fields.Char(string='Habitación')
    valor = fields.Float(string='Valor Total')
    estado = fields.Selection(string='Estado',selection=[('cancelado','Cancelado'),('pendiente','Pendiente'),('facturado','Facturado')])
    usuario = fields.Char(string='Usuario')

class PDFReporteDocumentos(models.AbstractModel):
    _name = 'report.motgama.reportedocumentos'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reportedocumentos'].sudo().browse(docids)
        count = len(docs)

        total = 0
        for doc in docs:
            total += doc.valor
        
        return {
            'docs': docs,
            'count': count,
            'total': "{:0,.1f}".format(total).replace(',','¿').replace('.',',').replace('¿','.')
        }