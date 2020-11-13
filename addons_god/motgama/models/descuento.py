from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaFlujoHabitación(models.Model):
    _inherit = 'motgama.flujohabitacion'
    
    @api.multi
    def agregar_descuento(self):
        if not self.env.ref('motgama.motgama_descuento_servicio') in self.env.user.permisos:
            raise Warning('No tiene permiso para agregar descuentos')
        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.descuento',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Agregar descuento'
        }

class MotgamaWizardDescuento(models.TransientModel):
    _name = 'motgama.wizard.descuento'
    _description = 'Motgama Wizard Descuento'

    habitacion = fields.Many2one(string='Habitación', comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    valorHosp = fields.Float(string='Total hospedaje',default=lambda self: self._get_valorHosp())
    valorDesc = fields.Float(string='Descontar')

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.model
    def _get_valorHosp(self):
        hab_id = self.env.context['active_id']
        hab = self.env['motgama.flujohabitacion'].browse(hab_id)
        return hab.orden_venta.amount_total

    @api.multi
    def agregar_descuento(self):
        self.ensure_one()
        ordenVenta = self.habitacion.orden_venta

        paramDesc = self.env['motgama.parametros'].search([('codigo','=','CODDESCSERV')],limit=1)
        if not paramDesc:
            raise Warning('Error: No existe el parámetro "CODDESCSERV"')
        prod_desc = self.env['product.template'].sudo().search([('default_code','=',paramDesc.valor)],limit=1)
        if not prod_desc:
            raise Warning('Error: No existe el producto de código "' + paramDesc.valor + '"')

        valores = {
            'customer_lead' : 0,
            'name' : prod_desc.name,
            'order_id' : ordenVenta.id,
            'price_unit' : 0.0 - self.valorDesc,
            'product_uom_qty' : 1,
            'product_id' : prod_desc.product_variant_id.id,
            'es_hospedaje' : False
        }
        nuevo = self.env['sale.order.line'].sudo().create(valores)
        if not nuevo:
            raise Warning('Error: No se pudo agregar el descuento')