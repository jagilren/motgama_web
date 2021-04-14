from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    movimiento = fields.Many2one(string='Movimiento',comodel_name='motgama.movimiento')
    es_hospedaje = fields.Boolean(default=False)
    asignafecha = fields.Datetime(string="Ingreso",compute="_compute_asignafecha",store=True)
    liquidafecha = fields.Datetime(string="Salida")

    @api.depends('movimiento')
    def _compute_asignafecha(self):
        for record in self:
            if record.movimiento:
                record.asignafecha = record.movimiento.asignafecha

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    es_hospedaje = fields.Boolean(string="¿Es hospedaje?",default=False)