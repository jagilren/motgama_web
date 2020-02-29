from odoo import models, fields, api
from odoo.exceptions import Warning

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
        
        sucursal = self.env['motgama.sucursal'].search([],limit=1).nombre
        for cuenta in saldos:
            for asociado in saldos[cuenta]:
                valores = {
                    'cod_cuenta': cuenta.code,
                    'comprobante': '',
                    'fecha': fields.Date().today(),
                    'documento': '',
                    'referencia': '',
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

        # TODO: Generar CSV
        
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
    sucursal = fields.Char(string='Sucursal')