from odoo import models, fields, api
from odoo.exceptions import Warning

class WizardReporteHospedaje(models.TransientModel):
    _name = 'motgama.wizard.reportehospedaje'

    fecha_inicial = fields.Datetime(string='Fecha Inicial',required=True)
    fecha_final = fields.Datetime(string= 'Fecha final',required=True)
    recepcion = fields.Many2one(string='Recepcion',comodel_name='motgama.recepcion')

    @api.multi
    def get_report(self):
        self.ensure_one()

        paramOcasional = self.env['motgama.parametros'].sudo().search([('codigo','=','CODHOSOCASIO')],limit=1)
        if not paramOcasional:
            raise Warning('No se ha definido el parámetro CODHOSOCASIO, contacte al administrador')
        paramAmanecida = self.env['motgama.parametros'].sudo().search([('codigo','=','CODHOSAMANE')],limit=1)
        if not paramAmanecida:
            raise Warning('No se ha definido el parámetro CODHOSAMANE, contacte al administrador')
        paramAdicional = self.env['motgama.parametros'].sudo().search([('codigo','=','CODHOSADCNAL')],limit=1)
        if not paramAmanecida:
            raise Warning('No se ha definido el parámetro CODHOSADCNAL, contacte al administrador')

        movimientos = self.env['motgama.movimiento'].sudo().search([('asignafecha','>',self.fecha_inicial),('asignafecha','<',self.fecha_final),('asignatipo','in',['OO','OA']),'|',('active','=',True),('active','=',False)])
        if not movimientos:
            raise Warning('No hay movimientos que mostrar')

        hospedajes = self.env['motgama.reportehospedaje'].sudo().search([])
        for hospedaje in hospedajes:
            hospedaje.unlink()

        ids = []
        for movimiento in movimientos:
            if not self.recepcion:
                ids.append(movimiento)
            else:
                if movimiento.habitacion_id.zona_id.recepcion_id.id == self.recepcion.id:
                    ids.append(movimiento)
        
        for movimiento in ids:
            factura = movimiento.factura
            if not factura:
                continue

            for line in factura.invoice_line_ids:
                valores = {
                    'recepcion': movimiento.habitacion_id.zona_id.recepcion_id.nombre,
                    'fecha': movimiento.asignafecha,
                    'habitacion': movimiento.habitacion_id.codigo,
                    'usuario': movimiento.recauda_uid.name
                }
                if line.product_id.default_code == paramOcasional.valor:
                    valores.update({'tipoHospedaje':'O'})
                elif line.product_id.default_code == paramAmanecida.valor:
                    valores.update({'tipoHospedaje':'AM'})
                elif line.product_id.default_code == paramAdicional.valor:
                    valores.update({'tipoHospedaje':'AD'})
                else:
                    continue
                valores.update({'valor':line.price_unit})
                nuevo = self.env['motgama.reportehospedaje'].sudo().create(valores)
                if not nuevo:
                    raise Warning('No se pudo crear el reporte')

        return{
            'name': 'Reporte de hospedaje',
            'view_mode':'tree',
            'view_id': self.env.ref('motgama.tree_reporte_hospedaje').id,
            'res_model': 'motgama.reportehospedaje',
            'type': 'ir.actions.act_window',
            'context': {'search_default_groupby_tipo': 1},
            'target': 'main'
        } 

class ReporteHospedaje(models.TransientModel):
    _name = 'motgama.reportehospedaje'

    recepcion = fields.Char(string='Recepción')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Char(string='Habitación')
    tipoHospedaje = fields.Selection(string='Tipo de hospedaje',selection=[('O','Hospedaje Ocasional'),('AM','Hospedaje Amanecida'),('AD','Hospedaje Adicional')])
    valor = fields.Float(string='Valor')
    usuario = fields.Char(string='Usuario')

class PDFReporteHospedaje(models.AbstractModel):
    _name = 'report.motgama.reportehospedaje'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reportehospedaje'].sudo().browse(docids)

        hospedajes = {}
        total = 0
        for doc in docs:
            tipoHospedaje = 'Hospedaje Ocasional' if doc.tipoHospedaje == 'O' else 'Hospedaje Amanecida' if doc.tipoHospedaje == 'AM' else 'Hospedaje Adicional' if doc.tipoHospedaje == 'AD' else ''
            if tipoHospedaje in hospedajes:
                hospedajes[tipoHospedaje] += doc.valor
            else:
                hospedajes[tipoHospedaje] = doc.valor
            total += doc.valor
        
        return {
            'company': self.env['res.company']._company_default_get('account.invoice'),
            'docs': docs,
            'hospedajes': hospedajes,
            'total': "{:0,.1f}".format(total).replace(',','¿').replace('.',',').replace('¿','.')
        }