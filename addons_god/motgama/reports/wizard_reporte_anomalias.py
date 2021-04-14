from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaWizardReporteAnomalias(models.TransientModel):
    _name = 'motgama.wizard.reporteanomalias'
    _description = 'Wizard Reporte Anomalías'

    tipo = fields.Selection(string="Tipo de reporte",selection=[('factura','Por fecha de factura'),('anomalia','Por fecha de anomalía')],default='factura')
    fecha_inicial = fields.Datetime(string="Fecha inicial", required=True)
    fecha_final = fields.Datetime(string="Fecha final", required=True)

    @api.model
    def check_permiso(self):
        if self.env.ref('motgama.motagama_informe_anomalias') not in self.env.user.permisos:
            raise Warning('No tiene permitido generar este informe')
        
        return {
            'type': 'ir.actions.act_window',
            'name': "Reporte de anomalías",
            'res_model': "motgama.wizard.reporteanomalias",
            'view_mode': "form",
            'target': "new"
        }

    @api.multi
    def get_report(self):
        self.ensure_one()

        domain = [('factura_anomalia','=',True)]
        if self.tipo == 'factura':
            domain.append(('create_date','>=',self.fecha_inicial))
            domain.append(('create_date','<=',self.fecha_final))
        elif self.tipo == 'anomalia':
            domain.append(('fecha_anomalia','<=',self.fecha_final))
            domain.append(('fecha_anomalia','>=',self.fecha_inicial))
        else:
            raise Warning('Debe seleccionar un tipo de reporte')

        facturas = self.env['account.invoice'].search(domain)
        if not facturas:
            raise Warning('No hay facturas con anomalía dentro del rango de fechas especificado')

        reporte = self.env['motgama.reporteanomalias'].search([])
        for o in reporte:
            o.unlink()
        
        for factura in facturas:
            valores = {
                'fecha_inicial': self.fecha_inicial,
                'fecha_final': self.fecha_final,
                'numero': factura.number,
                'fecha_factura': factura.date_invoice,
                'fecha_anomalia': factura.fecha_anomalia,
                'motivo_anomalia': factura.motivo_anomalia
            }
            reporte = self.env['motgama.reporteanomalias'].create(valores)
            if not reporte:
                raise Warning('No fue posible generar el reporte')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reporte de anomalías',
            'res_model': 'motgama.reporteanomalias',
            'view_mode': 'tree'
        }

class MotgamaReporteAnomalias(models.TransientModel):
    _name = 'motgama.reporteanomalias'
    _description = 'Reporte de Anomalías'

    fecha_inicial = fields.Datetime(string="Fecha inicial")
    fecha_final = fields.Datetime(string="Fecha final")
    numero = fields.Char(string="Número")
    fecha_factura = fields.Date(string="Fecha de factura")
    fecha_anomalia = fields.Datetime(string="Fecha de anomalía")
    motivo_anomalia = fields.Text(string="Motivo de anomalía")

class PDFReporteAnomalias(models.AbstractModel):
    _name = 'report.motgama.plantilla_reporte_anomalias'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reporteanomalias'].browse(docids)

        return {
            'docs': docs,
            'fecha_inicial': docs[0].fecha_inicial,
            'fecha_final': docs[0].fecha_final
        }