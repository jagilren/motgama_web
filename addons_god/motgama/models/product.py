from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = 'product.category'

    llevaComanda = fields.Boolean(string='¿Lleva Comanda?',default=False)
    es_hospedaje = fields.Boolean(string='Servicio de hospedaje',default=False)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    es_hospedaje = fields.Boolean(string='Servicio de hospedaje',default=False)

    @api.onchange('categ_id')
    def _onchange_categ(self):
        for record in self:
            if record.categ_id:
                record.es_hospedaje = record.categ_id.es_hospedaje