from odoo import models, fields, api

class MotgamaWizardReporteAnomalias(models.TransientModel):
    _name = 'motgama.wizard.reporteanomalias'
    _description = 'Wizard Reporte Anomalías'

    tipo = fields.Selection(string="Tipo de reporte",selection=[('factura','Por fecha de factura'),('anomalia','Por fecha de anomalía')],default='factura')
    fecha_inicial = fields.Datetime(string="Fecha inicial", required=True)
    fecha_final = fields.Datetime(string="Fecha final", required=True)

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

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reporte de anomalías',
            'res_model': 'account.invoice',
            'view_mode': 'tree,form',
            'views': [['motgama.view_reporte_anomalias','tree'],['account.invoice_form','form']],
            'domain': domain
        }