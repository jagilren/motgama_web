from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaPrendas(models.Model):
#    Fields: Prenda: el cliente deja elementos en forma de pago Creado: Mayo 10 del 2019                                        
    _name = 'motgama.prendas'
    _description = 'Registro de prendas'
    _rec_name = 'nroprenda'

    nroprenda = fields.Char(string='Nro.', readonly=True,required=True,copy=False,default='Nuevo')
    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion') # Habitacion del cliente que dejo la prende como pago                                 #P7.0.4R
    movimiento_id = fields.Integer('Movimiento')
    factura = fields.Many2one(string='Factura',comodel_name='account.invoice')
    creado_uid = fields.Many2one(string='Usuario que recibe la prenda',comodel_name='res.users',default=lambda self: self.env.user.id)
    tipovehiculo = fields.Selection(string='Tipo de vehiculo',selection=[('particular', 'Particular'), ('moto', 'Moto'), ('peaton', 'Peatón'),('taxi','Taxi')])
    placa = fields.Char(string='Placa')
    fecha = fields.Datetime(string='Fecha', default=lambda self: fields.Datetime().now())
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    descripcion = fields.Text(string='Descripción')
    valorprenda = fields.Float(string='Valor estimado de la prenda')
    valordeuda = fields.Float(string='Valor de la deuda')
    pagado = fields.Boolean(string='Pagado')
    pagadofecha = fields.Datetime(string='Fecha del pago')
    pago_uid = fields.Many2one(comodel_name='res.users',string='Usuario que recauda la prenda')
    recaudo = fields.Many2one(comodel_name='motgama.recaudo',readonly=True,string='Recaudo')
    active = fields.Boolean(string=u'Activo?',default=True)

    @api.model
    def create(self,values):
        if values.get('nroprenda','Nuevo') == 'Nuevo':
            values['nroprenda'] = self.env['ir.sequence'].next_by_code('motgama.prenda') or 'Nuevo'
        return super().create(values)
        
    @api.multi
    def recaudo_prenda(self):
        if not self.env.ref('motgama.motgama_recauda_prenda') in self.env.user.permisos:
            raise Warning('No tiene permitido recaudar prendas, contacte al administrador')
        return {
            'name': 'Recaudar prenda',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardprenda',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('motgama.form_wizard_prenda').id,
            'target': 'new'
        }