from odoo import models, fields, api
from odoo.exceptions import Warning

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    es_hospedaje = fields.Boolean(string="¿Es hospedaje?",default=False)

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    def button_continuar(self):
        self.ensure_one()
        movimiento = self.ultmovimiento

        ordenVieja = self.env['sale.order'].search([('movimiento','=',movimiento.id),('state','=','sale')],limit=1)
        if not ordenVieja:
            raise Warning('La habitación no fue correctamente liquidada')

        valores = {
            'partner_id' : ordenVieja.partner_id.id,
            'movimiento' : movimiento.id
        }
        ordenNueva = self.env['sale.order'].create(valores)
        if not ordenNueva:
            raise Warning('Error al crear nueva orden de venta')
        ordenNueva.action_confirm()

        lines = ordenVieja.order_line
        for line in lines:
            if not line.es_hospedaje:
                line.write({'order_id': ordenNueva.id})
        pickings = ordenVieja.picking_ids
        for picking in pickings:
            picking.write({'sale_id': ordenNueva.id})
        ordenVieja.action_cancel()
        if not ordenVieja.state == 'cancel':
            raise Warning('No se pudo cancelar la orden de venta')

        lines = ordenNueva.order_line
        for line in lines:
            valores = {
                'customer_lead' : line.customer_lead,
                'name' : line.name,
                'order_id' : ordenVieja.id,
                'price_unit' : line.price_unit,
                'product_uom_qty' : line.product_uom_qty,
                'product_id' : line.product_id.id
            }
            self.env['sale.order.line'].create(valores)

        estado = movimiento.asignatipo
        self.write({'estado': estado})
        
