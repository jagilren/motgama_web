from odoo import models, fields, api
from odoo.exceptions import Warning

class Invoice(models.Model):
    _inherit = 'account.invoice'

    factura_anomalia = fields.Boolean(string="Factura con anomalía")
    motivo_anomalia = fields.Char(string="Motivo de la anomalía")
    fecha_anomalia = fields.Datetime(string="Fecha y hora de la anomalía")
    fecha = fields.Datetime(string='Fecha y hora')
    es_hospedaje = fields.Boolean(default=False)
    habitacion_id = fields.Many2one(string='Habitación',comodel_name="motgama.flujohabitacion")
    recaudo = fields.Many2one(string='Recaudo',comodel_name='motgama.recaudo',ondelete='set null')
    recaudo_ids = fields.One2many(string='Recaudos',comodel_name='motgama.recaudo',inverse_name='factura')
    asignafecha = fields.Datetime(string="Ingreso")
    liquidafecha = fields.Datetime(string="Salida")
    lleva_prenda = fields.Boolean(string='Lleva prenda',default=False)
    prenda_id = fields.Many2one(string='Prenda',comodel_name='motgama.prendas')
    factura_electronica = fields.Boolean(string="Factura Electrónica",default=False)
    movimiento_id = fields.Many2one(string="Movimiento",comodel_name="motgama.movimiento")
    rectificativa = fields.Boolean(string="Factura Rectificativa",default=False)
    usuario_id = fields.Many2one(string="Usuario que genera",comodel_name="res.users",default=lambda self: self.env.user.id)

    @api.multi
    def registro_anomalia(self):
        if self.env.ref('motgama.motgama_factura_anomalia') not in self.env.user.permisos:
            raise Warning('No tiene permitido registrar anomalías')
        
        return {
            'name': 'Registrar anomalía',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.anomalia',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.view_wizard_anomalia').id,
            'target': 'new'
        }

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        values = super()._prepare_refund(invoice,date_invoice=date_invoice,date=date,description=description,journal_id=journal_id)
        if invoice.movimiento_id:
            values['movimiento_id'] = invoice.movimiento_id.id
            values['habitacion_id'] = invoice.habitacion_id.id
        values['rectificativa'] = True
        values['fecha'] = fields.Datetime().now()
        return values

    @api.model
    def create(self, values):
        if values['type'] in ['in_invoice','in_refund']:
            if self.env.ref('motgama.motgama_factura_proveedor') not in self.env.user.permisos:
                raise Warning('No tiene permitido registrar facturas o notas crédito de proveedor')
        return super().create(values)

class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    @api.multi
    def invoice_refund(self):
        result = super().invoice_refund()
        if 'res_id' in result:
            invoice = self.env['account.invoice'].sudo().browse(self.env.context['active_id'])
            if invoice.movimiento_id:
                new_invoice = self.env['account.invoice'].sudo().browse(result['res_id'])
                new_invoice.write({'movimiento_id': invoice.movimiento_id.id,'habitacion_id': invoice.habitacion_id.id})
        return result

class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    base_line = fields.Many2one(string="Línea de base de descuento",comodel_name="account.invoice.line")

class PDFFactura(models.AbstractModel):
    _name = 'report.motgama.formato_factura'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['account.invoice'].sudo().browse(docids)

        paramImpHab = self.env['motgama.parametros'].search([('codigo','=','IMPHABENFACTURA')], limit=1)
        if paramImpHab:
            if paramImpHab.valor == 's' or paramImpHab.valor == 'S':
                impHab = True
            else:
                impHab = False
        else:
            impHab = False

        return {
            'docs': docs,
            'impHab': impHab
        }