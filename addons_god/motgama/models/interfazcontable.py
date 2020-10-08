from odoo import models, fields, api
from odoo.exceptions import Warning

import csv
import base64
from datetime import datetime, timedelta

class MotgamaWizardInterfazContable(models.TransientModel):
    _name = 'motgama.wizard.interfazcontable'
    _description = 'Wizard Interfaz Contable'

    nueva = fields.Boolean(string='Nueva Interfaz (aumenta consecutivo)',default=False)
    repite = fields.Boolean(string='Repetir interfaz',default=False)

    fecha_inicial = fields.Datetime(string='Fecha inicial')
    fecha_final = fields.Datetime(string='Fecha final')
    genera_csv = fields.Boolean(string='Genera CSV',default=False)

    repite_id = fields.Many2one(string='Interfaz a repetir',comodel_name='motgama.interfazcontable.registro')

    es_manual = fields.Boolean(string='Es manual',default=True)

    @api.onchange('nueva')
    def _onchange_nueva(self):
        for record in self:
            if record.nueva:
                record.repite = False

    @api.multi
    def repite_interfaz(self):
        self.ensure_one()

        ruta = '/home/usr/files/'
        nom_arch = str(self.repite_id.fecha_inicial) + '.csv'
        ruta_arch = ruta + nom_arch
        with open(ruta_arch,newline='') as f:
            interfaz = self.env['motgama.interfazcontable'].search([])
            for reg in interfaz:
                reg.unlink()
            reader = csv.DictReader(f,delimiter=';',quotechar='"',fieldnames=['cod_cuenta','comprobante','fecha','documento','referencia','nit','nom_cuenta','tipo','valor','base','sucursal'])
            for row in reader:
                nuevo = self.env['motgama.interfazcontable'].create(row)
                if not nuevo:
                    raise Warning('No fue posible generar la interfaz')
            return {
                'name': 'Interfaz Contable',
                'view_mode': 'tree',
                'view_id': self.env.ref('motgama.motgama_interfaz_contable').id,
                'res_model': 'motgama.interfazcontable',
                'type': 'ir.actions.act_window',
                'target':'main'
            }
        raise Warning('Error al abrir el archivo, es probable que ya no exista o no fue posible acceder a él')

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
        if self.nueva:
            doc = self.env['ir.sequence'].next_by_code('motgama.interfazcontable.documento') or ''
        else:
            doc = ''

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
                    fecha = linea.fecha.strftime('%Y%m%d')
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
                    'datas_fname': nom_arch,
                    'res_model': 'motgama.interfazcontable',
                    'mimetype': 'text/csv'
                }
                arch = self.env['ir.attachment'].create(valores)
                
                paramCorreo = self.env['motgama.parametros'].search([('codigo','=','EMAILINTERFAZ')],limit=1)
                if not paramCorreo:
                    raise Warning('No se ha definido el parámetro "EMAILINTERFAZ"')
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
                    'body_html': html
                }
<<<<<<< HEAD:custom_addons/motgama/models/interfazcontable.py
                return valoresCorreo, arch, doc
=======
                correo = self.env['mail.mail'].create(valoresCorreo)
                if correo:
                    correo.sudo().send()
                
                valoresInterfaz = {
                    'nombre': doc if doc != '' else str(self.fecha_final),
                    'fecha_final': self.fecha_final,
                    'fecha_inicial': self.fecha_inicial,
                    'correo': correo.id
                }
                reg = self.env['motgama.interfazcontable.registro'].sudo().create(valoresInterfaz)
                if not reg:
                    raise Warning('No fue posible crear la interfaz contable')
>>>>>>> correo2:addons_god/motgama/models/interfazcontable.py
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

class MotgamaInterfazContableRegistro(models.Model):
    _name = 'motgama.interfazcontable.registro'
    _description = 'Historial de interfaces contables'
    _order = 'fecha_inicial desc'

    nombre = fields.Char(string='Documento',readonly=True)
    correo = fields.Many2one(string='Archivo adjunto',comodel_name='mail.mail',readonly=True)
    fecha_inicial = fields.Datetime(string='Fecha inicial',readonly=True)
    fecha_final = fields.Datetime(string='Fecha final',readonly=True,required=True)

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = rec.nombre + ', ' + str(rec.fecha_inicial)
            res.append((rec.id,name))
        return res

    @api.model
    def check_hora(self):
        fecha = self.get_hora()
        if fecha < datetime.now() < fecha + timedelta(minutes=5):
            self.generar_interfaz()

    @api.model
    def get_hora(self):
        paramHora = self.env['motgama.parametros'].search([('codigo','=','HORACIERRE')],limit=1)
        fecha_actual = datetime.now()
        if not paramHora:
            raise Warning('No se ha definido el parámetro "HORACIERRE"')
        horaTz = datetime.strptime(paramHora.valor,'%H:%M')
        hora = horaTz + timedelta(hours=5)

        return datetime(fecha_actual.year,fecha_actual.month,fecha_actual.day,hora.hour,hora.minute)

    @api.model
    def generar_interfaz(self):
        fecha_final = fields.Datetime().now()
        interfaces = self.env['motgama.interfazcontable.registro'].search([],order='create_date desc')
        if not interfaces:
            fecha_inicial = datetime(2020,1,1)
        else:
            fecha_inicial = interfaces[0].fecha_final + timedelta(milliseconds=1)
        
        valores = {
            'fecha_inicial': fecha_inicial,
            'fecha_final': fecha_final,
            'genera_csv': True,
            'es_manual': False
        }
        nuevo = self.env['motgama.wizard.interfazcontable'].create(valores)
        if not nuevo:
            raise Warning('No fue posible generar el reporte')
        
        valores_correo, arch, doc = nuevo.get_report()

        valores_reporte = {
            'tipo_reporte': 'fecha',
            'fecha_inicial': fecha_inicial,
            'fecha_final': fecha_final,
            'es_manual': False
        }
        reporte = self.env['motgama.wizard.reporteventas'].create(valores_reporte)
        
        reporte.get_report()
        reporte_ventas = self.env['motgama.reporteventas'].search([])

        pdf = self.env['report'].sudo().get_pdf(reporte_ventas.ids, 'motgama.reporte_ventas')
        attachment_report = self.env['ir.attachment'].create({
            'name': 'Reporte de ventas',
            'type': 'binary',
            'datas': base64.encodestring(pdf),
            'res_model': 'motgama.reporteventas',
            'mimetype': 'application/x-pdf'
        })

        valores_correo.update({'attachment_ids': [(6,0,[attachment_report.id, arch.id])]})
        correo = self.env['mail.mail'].create(valores_correo)
        if correo:
            correo.sudo().send()
        
        valoresInterfaz = {
            'nombre': doc if doc != '' else str(fecha_final),
            'fecha_final': fecha_final,
            'fecha_inicial': fecha_inicial,
            'correo': correo.id
        }
        reg = self.env['motgama.interfazcontable.registro'].create(valoresInterfaz)
        if not reg:
            raise Warning('No fue posible crear la interfaz contable')