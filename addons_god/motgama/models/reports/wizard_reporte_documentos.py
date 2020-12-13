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

    @api.model
    def check_permiso(self):
        if self.env.ref('motgama.motgama_informe_documentos') not in self.env.user.permisos:
            raise Warning('No tiene permitido generar este informe')
        
        return {
            'type': 'ir.actions.act_window',
            'name': "Reporte de documentos",
            'res_model': "motgama.wizard.reportedocumentos",
            'view_mode': "form",
            'target': "new"
        }

    @api.multi
    def get_report(self):
        self.ensure_one()

        if self.tipo_reporte == 'fecha':
            docs = self.env['sale.order'].search(['|','&',('movimiento','!=',False),'&',('liquidafecha','!=',False),'&',('liquidafecha','>',self.fecha_inicial),('liquidafecha','<',self.fecha_final),'&',('create_date','<',self.fecha_final),('create_date','>',self.fecha_inicial)])
        elif self.tipo_reporte == 'documento':
            id_inicial = self.doc_inicial.id
            id_final = self.doc_final.id
            docs = self.env['sale.order'].search([('id','<=',id_final),('id','>=',id_inicial)])
        else:
            raise Warning('Seleccione un tipo de reporte')
        if not docs:
            raise Warning('No hay documentos que mostrar')

        reporte = self.env['motgama.reportedocumentos'].search([])
        for doc in reporte:
            doc.unlink()
        
        for doc in docs:
            valores = {
                'tipo_reporte': self.tipo_reporte,
                'fecha_inicial': self.fecha_inicial if self.fecha_inicial else False,
                'fecha_final': self.fecha_final if self.fecha_final else False,
                'doc_inicial': self.doc_inicial.name if self.doc_inicial else False,
                'doc_final': self.doc_final.name if self.doc_final else False,
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
            
            nuevo = self.env['motgama.reportedocumentos'].create(valores)
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

    tipo_reporte = fields.Char(string='Tipo reporte')
    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')
    doc_inicial = fields.Char(string="Documento inicial")
    doc_final = fields.Char(string="Documento final")

    fecha = fields.Datetime(string='Fecha')
    doc = fields.Char(string='Documento')
    cliente = fields.Char(string='Cliente')
    habitacion = fields.Char(string='Habitación')
    valor = fields.Float(string='Valor Total')
    estado = fields.Selection(string='Estado',selection=[('cancelado','Cancelado'),('pendiente','Pendiente'),('facturado','Facturado')])
    usuario = fields.Char(string='Usuario')

class PDFReporteDocumentos(models.AbstractModel):
    _name = 'report.motgama.reportedocumentos'

    tipos_reporte = {
        'fecha': 'entre las fechas',
        'documento': 'entre los documentos'
    }

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reportedocumentos'].browse(docids)
        count = len(docs)

        total = 0
        for doc in docs:
            total += doc.valor
        
        return {
            'tipo_reporte': docs[0].tipo_reporte,
            'tipos_reporte': self.tipos_reporte,
            'company': self.env['res.company']._company_default_get('account.invoice'),
            'sucursal': self.env['motgama.sucursal'].search([],limit=1),
            'docs': docs,
            'count': count,
            'total': "{:0,.1f}".format(total).replace(',','¿').replace('.',',').replace('¿','.')
        }