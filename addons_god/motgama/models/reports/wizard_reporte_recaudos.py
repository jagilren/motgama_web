from odoo import fields, models, api
from odoo.exceptions import Warning

class WizardReporteRecaudos(models.TransientModel):
    _name = 'motgama.wizard.reporterecaudos'
    _description = 'Wizard del Reporte de Recaudos'

    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')
    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')
    incluye_habitaciones = fields.Boolean(string='Incluir facturado a habitaciones',default=True)
    incluye_abonos = fields.Boolean(string='Incluir abonos',default=True)
    incluye_prendas = fields.Boolean(string='Incluir prendas',default=True)
    incluye_anticipos = fields.Boolean(string='Incluir anticipos',default=True)
    incluye_otros = fields.Boolean(string='Incluir otros recaudos',default=True)

    @api.model
    def check_permiso(self):
        if self.env.ref('motgama.motgama_informe_recaudos') not in self.env.user.permisos:
            raise Warning('No tiene permitido generar este informe')
        
        return {
            'type': 'ir.actions.act_window',
            'name': "Reporte de recaudos",
            'res_model': "motgama.wizard.reporterecaudos",
            'view_mode': "form",
            'target': "new"
        }

    @api.multi
    def get_report(self):
        self.ensure_one()

        domain = [('create_date','>',self.fecha_inicial),('create_date','<',self.fecha_final)]
        incluye = []
        if self.incluye_abonos:
            incluye.append('abonos')
        if self.incluye_anticipos:
            incluye.append('anticipos')
        if self.incluye_habitaciones:
            incluye.append('habitaciones')
        if self.incluye_otros:
            incluye.append('otros')
        if self.incluye_prendas:
            incluye.append('prenda')
        if not incluye:
            raise Warning('Seleccione algo para incluir en el reporte')
        domain.append(('tipo_recaudo','in',incluye))

        recaudos = self.env['motgama.recaudo'].search(domain)
        if not recaudos:
            raise Warning('No hay recaudos que mostrar')

        reporte = self.env['motgama.reporterecaudos'].search([])
        if reporte:
            for recaudo in reporte:
                recaudo.unlink()

        for recaudo in recaudos:
            if self.recepcion:
                if recaudo.habitacion:
                    if recaudo.habitacion.recepcion.id != self.recepcion.id:
                        continue
                else:
                    invoice = self.env['account.invoice'].search([('recaudo','=',recaudo.id)],limit=1)
                    if invoice:
                        factura = self.env['motgama.facturaconsumos'].search([('factura_id','=',invoice.id)],limit=1)
                        if factura:
                            if factura.recepcion.id != self.recepcion.id:
                                continue
            for pago in recaudo.pagos:
                valores = {
                    'nrorecaudo': recaudo.nrorecaudo,
                    'fecha': recaudo.create_date,
                    'medio_pago': pago.mediopago.nombre,
                    'valor': pago.valor,
                    'usuario': recaudo.usuario_uid.name,
                    'tipo_recaudo': recaudo.tipo_recaudo
                }
                if pago.mediopago.tipo in ['abono']:
                    continue
                if pago.mediopago.diario_id:
                    valores.update({'diario':pago.mediopago.diario_id.name})
                if recaudo.habitacion:
                    valores.update({
                        'recepcion':recaudo.recepcion_id.nombre,
                        'habitacion':recaudo.habitacion.codigo
                    })
                elif self.recepcion:
                    valores.update({'recepcion':self.recepcion.nombre})
                else:
                    invoice = self.env['account.invoice'].search([('recaudo','=',recaudo.id)],limit=1)
                    if invoice:
                        factura = self.env['motgama.facturaconsumos'].search([('factura_id','=',invoice.id),('active','=',False)],limit=1)
                        if factura:
                            valores.update({'recepcion':factura.recepcion.nombre})
                nuevo = self.env['motgama.reporterecaudos'].create(valores)
                if not nuevo:
                    raise Warning('No se pudo generar el reporte')
        
        reporte = self.env['motgama.reporterecaudos'].search([])
        if not reporte:
            raise Warning('No hay recaudos que mostrar')

        return {
            'name': 'Reporte de recaudos',
            'view_mode':'tree',
            'view_id': self.env.ref('motgama.tree_reporte_recaudos').id,
            'res_model': 'motgama.reporterecaudos',
            'type': 'ir.actions.act_window',
            'target': 'main'
        }

class MotgamaReporteRecaudos(models.TransientModel):
    _name = 'motgama.reporterecaudos'
    _description = 'Reporte de Recaudos'

    nrorecaudo = fields.Char(string='Nro. Recaudo')
    recepcion = fields.Char(string='Recepción')
    fecha = fields.Datetime(string='Fecha')
    habitacion = fields.Char(string='Habitación')
    tipo_recaudo = fields.Selection(string='Tipo de Recaudo',selection=[('habitaciones','Recaudo de habitaciones'),('abonos','Recaudo de abonos'),('prenda','Recaudo de prenda'),('anticipos','Recaudo de anticipos'),('otros','Otros recaudos')])
    diario = fields.Char(string='Diario de pagos')
    medio_pago = fields.Char(string='Medio de pago')
    valor = fields.Float(string='Valor')
    usuario = fields.Char(string='Usuario')

class PDFReporteRecaudos(models.AbstractModel):
    _name = 'report.motgama.reporterecaudos'

    @api.model
    def _get_report_values(self,docids,data=None):
        docs = self.env['motgama.reporterecaudos'].browse(docids)

        tiposRecaudo = {}
        mediosPago = {}
        habitaciones = []
        total = 0.0
        for doc in docs:
            total += doc.valor
            if doc.tipo_recaudo == 'habitaciones':
                tipo = 'Recaudo de habitaciones'
            elif doc.tipo_recaudo == 'abonos':
                tipo = 'Recaudo de abonos'
            elif doc.tipo_recaudo == 'prenda':
                tipo = 'Recaudo de prenda'
            elif doc.tipo_recaudo == 'anticipos':
                tipo = 'Recaudo de anticipos'
            else:
                tipo = 'Otros recaudos'

            if tipo in tiposRecaudo:
                tiposRecaudo[tipo] += doc.valor
            else:
                tiposRecaudo[tipo] = doc.valor

            if not doc.habitacion in habitaciones:
                habitaciones.append(doc.habitacion)
            
            if doc.medio_pago in mediosPago:
                mediosPago[doc.medio_pago] += doc.valor
            else:
                mediosPago[doc.medio_pago] = doc.valor
        
        for tipo in tiposRecaudo:
            tiposRecaudo[tipo] = "{:0,.2f}".format(tiposRecaudo[tipo]).replace(',','¿').replace('.',',').replace('¿','.')
        for medio in mediosPago:
            mediosPago[medio] = "{:0,.2f}".format(mediosPago[medio]).replace(',','¿').replace('.',',').replace('¿','.')
        total = "$ " + "{:0,.2f}".format(total).replace(',','¿').replace('.',',').replace('¿','.')
        
        return {
            'company': self.env['res.company']._company_default_get('account.invoice'),
            'sucursal': self.env['motgama.sucursal'].search([],limit=1),
            'docs': docs,
            'tipos': tiposRecaudo,
            'medios': mediosPago,
            'habitaciones': len(habitaciones),
            'total': total
        }