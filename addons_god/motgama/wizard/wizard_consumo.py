from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import Warning

class MotgamaWizardConsumos(models.TransientModel):
    _name = 'motgama.wizard.consumos'
    _description = 'Wizard Consumos'

    habitacion_id = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    producto_id = fields.Many2one(string='Producto (Cod. Barras, Nombre, Código)',comodel_name='product.template')
    lugar_id = fields.Many2one(string='Recepción',comodel_name='stock.location')
    cambia_recepcion = fields.Boolean(string="Cambia Recepción",default=lambda self: self._get_cambia_recepcion())
    linea_ids = fields.Many2many(string='Consumos',comodel_name='motgama.wizard.consumos.line')
    total_prods = fields.Integer(string='Total items',compute='_compute_items')
    total_consumos = fields.Float(string='Total consumos',compute='_compute_total')
    consumo_ids = fields.Many2many(string='Consumos anteriores',comodel_name='motgama.consumo',default=lambda self: self._get_consumos())

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.model
    def _get_consumos(self):
        hab = self.env['motgama.flujohabitacion'].browse(self.env.context['active_id'])
        ids = [consumo.id for consumo in hab.consumos]
        return [(6,0,ids)]
    
    @api.onchange('habitacion_id')
    def _onchange_habitacion(self):
        for record in self:
            if record.habitacion_id:
                record.lugar_id = self.env['stock.location'].sudo().search([('recepcion','=',record.habitacion_id.recepcion.id)],limit=1)
    
    @api.onchange('producto_id')
    def _onchange_producto(self):
        for record in self:
            if record.producto_id and record.habitacion_id:
                movimiento = record.habitacion_id.ultmovimiento
                lista = movimiento.listaprecioproducto
                precioLista = self.env['product.pricelist.item'].sudo().search(['&',('pricelist_id','=',lista.id),('product_tmpl_id','=',record.producto_id.id)], limit=1)
                if not precioLista:
                    precio = record.producto_id.list_price
                else:
                    precio = precioLista.fixed_price

                if precio == 0.0:
                    permitecambiarvalor = True
                    valor = 0
                else:
                    permitecambiarvalor = False
                    valor = precio
                valores = {
                    'producto_id': record.producto_id.id,
                    'lugar_id': record.lugar_id.id,
                    'vlrUnitario': valor,
                    'vlrUnitario_save': valor,
                    'cantidad': 1,
                    'cambiar_valor': permitecambiarvalor,
                    'lleva_comanda': record.producto_id.categ_id.llevaComanda
                }
                record.linea_ids = [(0,0,valores)]
                record.producto_id = None
    
    @api.model
    def _get_cambia_recepcion(self):
        try:
            permiso = self.env.ref('motgama.motgama_consumo_recepcion') in self.env.user.permisos
            return permiso
        except ValueError:
            return False 

    @api.depends('linea_ids.cantidad')
    def _compute_items(self):
        for record in self:
            suma = 0
            for linea in record.linea_ids:
                suma += linea.cantidad
            record.total_prods = suma
    
    @api.depends('linea_ids.vlrSubtotal')
    def _compute_total(self):
        for record in self:
            suma = 0
            for linea in record.linea_ids:
                suma += linea.vlrSubtotal
            record.total_consumos = suma

    @api.multi
    def agregar_consumos(self):
        self.ensure_one()
        
        for linea in self.linea_ids:
            valores = {
                'recepcion': self.habitacion_id.recepcion.id,
                'llevaComanda': linea.lleva_comanda,
                'textoComanda': linea.comanda,
                'habitacion': self.habitacion_id.id,
                'movimiento_id': self.habitacion_id.ultmovimiento.id,
                'producto_id': linea.producto_id_save.id,
                'cantidad': linea.cantidad,
                'valorUnitario': linea.vlrUnitario_save,
                'vlrUnitario': linea.vlrUnitario_save,
                'vlrSubtotal': linea.vlrSubtotal_save,
                'lugar_id': linea.lugar_id.id,
                'asigna_uid': self.env.user.id,
                'permitecambiarvalor': linea.cambiar_valor
            }
            consumo = self.env['motgama.consumo'].create(valores)
            if not consumo:
                raise Warning('No se pudo registrar los consumos')
        self.habitacion_id.refresh_views()
        return True

class MotgamaLineaConsumos(models.TransientModel):
    _name = 'motgama.wizard.consumos.line'
    _description = 'Línea Wizard Consumos'

    producto_id = fields.Many2one(string='Producto',comodel_name='product.template')
    producto_id_save = fields.Many2one(string='Producto',comodel_name='product.template',compute="_producto_id_save",store=True)
    lugar_id = fields.Many2one(string='Recepción',comodel_name='stock.location')
    vlrUnitario = fields.Float(string='Valor Unitario')
    vlrUnitario_save = fields.Float(string='Valor Unitario')
    cambia_recepcion = fields.Boolean(string="Cambia recepción",compute="_compute_cambia_recepcion")
    cantidad = fields.Integer(string='Cantidad')
    vlrSubtotal = fields.Float(string='Subtotal',compute='_compute_subtotal',store=True)
    vlrSubtotal_save = fields.Float(string='Subtotal',compute='_vlrSubtotal_save',store=True)
    cambiar_valor = fields.Boolean(string='Puede cambiar valor',default=False)
    lleva_comanda = fields.Boolean(string='Lleva comanda',default=False)
    comanda = fields.Text(string='Comanda',default='')

    @api.depends()
    def _compute_cambia_recepcion(self):
        for record in self:
            self.cambia_recepcion = self.env.ref('motgama.motgama_consumo_recepcion') in self.env.user.permisos

    @api.depends('vlrUnitario_save','cantidad')
    def _compute_subtotal(self):
        for record in self:
            if record.vlrUnitario_save and record.cantidad:
                record.vlrSubtotal = record.vlrUnitario_save * record.cantidad
    
    @api.depends('producto_id')
    def _producto_id_save(self):
        for record in self:
            if self.producto_id:
                record.producto_id_save = record.producto_id
    
    @api.depends('vlrSubtotal')
    def _vlrSubtotal_save(self):
        for record in self:
            if self.vlrSubtotal:
                record.vlrSubtotal_save = record.vlrSubtotal

    @api.model
    def create(self,values):
        if not 'vlrUnitario_save' in values:
            values['vlrUnitario_save'] = values['vlrUnitario']
        return super().create(values)