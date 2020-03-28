from odoo import models, fields, api
from odoo.exceptions import Warning

import csv
import base64
from datetime import datetime

class MotgamaWizardInterfazContable(models.TransientModel):
    _name = 'motgama.wizard.interfazcontable'
    _description = 'Wizard Interfaz Contable'

    fecha_inicial = fields.Datetime(string='Fecha inicial',required=True)
    fecha_final = fields.Datetime(string='Fecha final',required=True)
    genera_csv = fields.Boolean(string='Genera CSV',default=False)

    @api.multi
    def get_report(self):
        self.ensure_one()

        apuntes = self.env['account.move.line'].search([('create_date','<=',self.fecha_final),('create_date','>=',self.fecha_inicial)])
        facturas = self.env['account.invoice'].search([('fecha','>=',self.fecha_inicial),('fecha','<=',self.fecha_final)])

        fact_inicial = '0'
        fact_final = '0'
        primera_fecha  = self.fecha_final
        ultima_fecha = self.fecha_inicial
        for factura in facturas:
            if factura.fecha < primera_fecha:
                primera_fecha = factura.fecha
                fact_inicial = factura.number
            if factura.fecha > ultima_fecha:
                ultima_fecha = factura.fecha
                fact_final = factura.number

        if len(fact_inicial) > 4:
            fact_inicial = fact_inicial[-4:]
        while len(fact_inicial) < 4:
            fact_inicial = ' ' + fact_inicial
        if len(fact_final) > 3:
            fact_final = fact_final[-3:]
        while len(fact_final) < 3:
            fact_final = ' ' + fact_final

        interfaz = self.env['motgama.interfazcontable'].search([])
        for record in interfaz:
            record.unlink()

        saldos = {}
        for apunte in apuntes:
            if apunte.account_id in saldos:
                if apunte.partner_id in saldos[apunte.account_id]:
                    saldos[apunte.account_id][apunte.partner_id] += apunte.debit - apunte.credit
                else:
                    saldos[apunte.account_id][apunte.partner_id] = apunte.debit - apunte.credit
            else:
                saldos[apunte.account_id] = {apunte.partner_id: apunte.debit - apunte.credit}

        paramComprobante = self.env['motgama.parametros'].search([('codigo','=','COMPROBANTE')],limit=1)
        if not paramComprobante:
            comp = ''
        else:
            comp = paramComprobante.valor
        paramSucursal = self.env['motgama.parametros'].search([('codigo','=','CCOSTO')],limit=1)
        if not paramSucursal:
            sucursal = ''
        else:
            sucursal = paramSucursal.valor
        doc = self.env['ir.sequence'].next_by_code('motgama.interfazcontable.documento') or ''

        lineas = []
        for cuenta in saldos:
            for asociado in saldos[cuenta]:
                valores = {
                    'cod_cuenta': cuenta.code,
                    'comprobante': comp,
                    'fecha': self.fecha_inicial,
                    'documento': doc,
                    'referencia': fact_inicial + '-' + fact_final,
                    'nit':  asociado.vat if asociado.vat != "1" else "",
                    'nom_cuenta': cuenta.name,
                    'tipo': 1 if saldos[cuenta][asociado] >= 0 else 2,
                    'valor': abs(saldos[cuenta][asociado]),
                    'base': 0,
                    'sucursal': sucursal
                }
                nuevo = self.env['motgama.interfazcontable'].create(valores)
                if not nuevo:
                    raise Warning('No se pudo cargar la interfaz contable')
                lineas.append(nuevo)

        if self.genera_csv:
            ruta = '/home/usr/files/'
            nom_arch = str(self.fecha_inicial) + '.csv'
            ruta_arch = ruta + nom_arch
            with open(ruta_arch,mode='w') as f1:
                writer = csv.writer(f1,delimiter=';',quotechar='"',quoting=csv.QUOTE_NONE)
                for linea in lineas:
                    cod_cuenta = linea.cod_cuenta
                    comprobante = linea.comprobante
                    fecha = datetime.strftime('%Y%m%d')
                    documento = linea.documento
                    referencia = linea.referencia
                    nit = '' if not linea.nit else str(linea.nit)
                    nom_cuenta = linea.nom_cuenta
                    tipo = linea.tipo
                    valor = linea.valor
                    base = 0
                    sucursal = linea.sucursal
                    row = [cod_cuenta,comprobante,fecha,documento,referencia,nit,nom_cuenta,tipo,valor,base,sucursal]
                    writer.writerow(row)
            with open(ruta_arch,mode='r',encoding='utf-8') as f2:
                data = str.encode(f2.read(),'utf-8')
                valores = {
                    'name': nom_arch,
                    'type': 'binary',
                    'datas': base64.encodestring(data),
                    'res_model': 'motgama.interfazcontable',
                    'mimetype': 'text/csv'
                }
                arch = self.env['ir.attachment'].create(valores)
                
                paramCorreo = self.env['motgama.parametros'].search([('codigo','=','EMAILSALARMAS')],limit=1)
                if not paramCorreo:
                    raise Warning('No se ha definido el parámetro "EMAILSALARMAS"')
                sucursal = self.env['motgama.sucursal'].search([],limit=1).nombre
                subject = sucursal + ': ' + nom_arch
                html = '<p>Interfaz contable de ' + sucursal + ' adjunta</p>'
                email_to = paramCorreo.valor
                mailserver = self.env['ir.mail_server'].sudo().search([],limit=1)
                if not mailserver:
                    email_from = ''
                else:
                    email_from = mailserver.smtp_user
                valoresCorreo = {
                    'subject': subject,
                    'email_from': email_from,
                    'email_to': email_to,
                    'body_html': html,
                    'author_id': False,
                    'attachment_ids': [(6,0,[arch.id])]
                }
                correo = self.env['mail.mail'].sudo().create(valoresCorreo)
                if correo:
                    correo.sudo().send()
        else:
            return {
                'name': 'Interfaz Contable',
                'view_mode': 'tree',
                'view_id': self.env.ref('motgama.motgama_interfaz_contable').id,
                'res_model': 'motgama.interfazcontable',
                'type': 'ir.actions.act_window',
                'target':'main'
            }

class MotgamaInterfazContable(models.TransientModel):
    _name = 'motgama.interfazcontable'
    _description = 'Interfaz Contable'

    cod_cuenta = fields.Char(string='Cuenta contable')
    comprobante = fields.Char(string='Comprobante')
    fecha = fields.Date(string='Fecha')
    documento = fields.Char(string='Documento')
    referencia = fields.Char(string='Referencia')
    nit = fields.Char(string='NIT')
    nom_cuenta = fields.Char(string='Nombre de cuenta')
    tipo = fields.Integer(string='Débito (1) / Crédito (2)')
    valor = fields.Float(string='Valor')
    base = fields.Float(string='Base')
    sucursal = fields.Char(string='Centro de costo')