from odoo import fields, models, api
from odoo.exceptions import Warning

class MotgamaFacturaConsumos(models.Model):
    _name = 'motgama.facturaconsumos'
    _description = 'Facturar consumos sin hospedaje'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre',compute='_compute_nombre',store=True)
    cliente_id = fields.Many2one(string='Cliente',comodel_name='res.partner',domain=[('customer','=',True)],default=lambda self: self._get_cliente())
    currency_id = fields.Many2one(comodel_name='res.currency',default=lambda self: self._get_currency())
    consumo_ids = fields.One2many(string='Consumos',comodel_name='motgama.lineafacturaconsumos',inverse_name='factura_id')
    valor_total = fields.Monetary(string='Valor total',compute='_compute_valor',store=True)
    factura_id = fields.Many2one(string='Factura', comodel_name='account.invoice')
    orden_venta = fields.Many2one(comodel_name='sale.order')
    active = fields.Boolean(string="Activo",default=True)
    recepcion = fields.Many2one(string='Recepción',comodel_name='motgama.recepcion')

    @api.model
    def _get_currency(self):
        return self.env['res.company']._company_default_get('account.invoice').currency_id.id

    @api.model
    def _get_cliente(self):
        return self.env['res.partner'].sudo().search([('vat','=','1')],limit=1).id

    @api.depends('factura_id')
    def _compute_nombre(self):
        for record in self:
            if record.factura_id:
                record.nombre = record.factura_id.number
            else:
                record.nombre = '[Sin facturar]'

    @api.depends('consumo_ids')
    def _compute_valor(self):
        for record in self:
            valor = 0.0
            for consumo in record.consumo_ids:
                valor += consumo.vlrSubtotal
            record.valor_total = valor

    @api.multi
    def btn_facturar(self):
        self.ensure_one()
        if len(self.consumo_ids) == 0:
            raise Warning('Ingrese consumos para facturar')
        if not self.env.ref('motgama.motgama_factura_extemporanea') in self.env.user.permisos:
            raise Warning('No tiene permitido facturar consumos sin hospedaje, contacte al administrador')
        return {
            'name': 'Recaudar factura',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizardfacturaconsumos',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_recaudo_consumos').id,
            'target': 'new'
        }

    @api.multi
    def unlink(self):
        for record in self:
            if record.factura_id:
                raise Warning('No se pueden eliminar consumos ya facturados')
            else:
                return super().unlink()

class MotgamaLineaFacturaConsumos(models.Model):
    _name = 'motgama.lineafacturaconsumos'
    _description = 'Línea de factura de consumos sin hospedaje'

    factura_id = fields.Many2one(string='Factura sin hospedaje', comodel_name='motgama.facturaconsumos',required=True)
    producto_id = fields.Many2one(string='Producto',comodel_name='product.template',required=True)
    cantidad = fields.Float(string='Cantidad')
    vlrUnitario = fields.Float(string='Valor Unitario')
    vlrSubtotal = fields.Float(string='Subtotal',compute='_compute_subtotal')
    permitecambiarvalor = fields.Boolean(string='Permite cambiar valor',default=False,compute="_compute_valor",store=True)

    @api.onchange('producto_id')
    def _compute_producto(self):
        for record in self:
            if record.producto_id:
                precio = record.producto_id.list_price
                if precio == 0.0:
                    record.permitecambiarvalor = True
                else:
                    record.permitecambiarvalor = False
                    record.vlrUnitario = precio

    @api.depends('cantidad','vlrUnitario')
    def _compute_subtotal(self):
        for record in self:
            record.vlrSubtotal = record.vlrUnitario * record.cantidad

    @api.model
    def create(self,values):
        prod = values['producto_id']
        if not 'vlrUnitario' in values:
            values['vlrUnitario'] = self.env['product.template'].sudo().search([('id','=',prod)],limit=1).list_price
        return super().create(values)