from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaFlujoHabitación(models.Model):
    _inherit = 'motgama.flujohabitacion'
    
    @api.multi
    def agregar_descuento(self):
        self.ensure_one()

        desc = self.env['motgama.descuento'].search([('movimiento_id','=',self.ultmovimiento.id)],limit=1)
        if desc:
            tiene_permiso = self.env.ref('motgama.motgama_edita_descuento') in self.env.user.permisos
            if not tiene_permiso:
                tiene_permiso = self.env.ref('motgama.motgama_elimina_descuento') in self.env.user.permisos
                if not tiene_permiso:
                    msg = 'No tiene permitido editar o eliminar descuentos por mal servicio'
        else:
            tiene_permiso = self.env.ref('motgama.motgama_descuento_servicio') in self.env.user.permisos
            if not tiene_permiso:
                msg = 'No tiene permitido agregar descuentos por mal servicio'

        if not tiene_permiso:
            raise Warning(msg)

        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'motgama.wizard.descuento',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Agregar descuento'
        }

class MotgamaDescuento(models.Model):
    _name = 'motgama.descuento'
    _description = 'Descuento'

    movimiento_id = fields.Many2one(string="Movimiento",comodel_name="motgama.movimiento")
    habitacion_id = fields.Many2one(string="Habitación",comodel_name='motgama.flujohabitacion')
    valorDesc = fields.Float(string="Valor descuento")
    linea_id = fields.Many2one(string="Línea de orden de venta",comodel_name="sale.order.line")
    usuario_id = fields.Many2one(string="Usuario",comodel_name="res.users")

    @api.multi
    def aplica_descuento(self):
        self.ensure_one()
        ordenVenta = self.habitacion_id.orden_venta

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

        self.sudo().write({'linea_id': nuevo.id})

class MotgamaWizardDescuento(models.TransientModel):
    _name = 'motgama.wizard.descuento'
    _description = 'Motgama Wizard Descuento'

    habitacion = fields.Many2one(string='Habitación', comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    valorHosp = fields.Float(string='Total hospedaje',default=lambda self: self._get_valorHosp())
    valorDesc = fields.Float(string='Valor descuento',default=lambda self: self._get_valorDesc())
    tipo = fields.Selection(string="Operación a realizar",selection=[('editar','Modificar'),('eliminar','Eliminar')],default=lambda self: self._get_tipo())
    cambia_tipo = fields.Boolean(string="Cambia tipo",default=lambda self: self._get_cambia_tipo())

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.model
    def _get_valorHosp(self):
        hab_id = self.env.context['active_id']
        hab = self.env['motgama.flujohabitacion'].browse(hab_id)
        if hab.estado == 'LQ':
            return hab.orden_venta.amount_total
        else:
            return 0.0

    @api.model
    def _get_valorDesc(self):
        hab_id = self.env.context['active_id']
        hab = self.env['motgama.flujohabitacion'].browse(hab_id)
        desc = self.env['motgama.descuento'].search([('movimiento_id','=',hab.ultmovimiento.id)],limit=1)
        if desc:
            return desc.valorDesc
        else:
            return 0.0

    @api.model
    def _get_tipo(self):
        hab_id = self.env.context['active_id']
        hab = self.env['motgama.flujohabitacion'].browse(hab_id)
        desc = self.env['motgama.descuento'].search([('movimiento_id','=',hab.ultmovimiento.id)],limit=1)
        if desc:
            if self.env.ref('motgama.motgama_edita_descuento') in self.env.user.permisos:
                return 'editar'
            else:
                return 'eliminar'
        else:
            return False

    @api.model
    def _get_cambia_tipo(self):
        return self.env.ref('motgama.motgama_edita_descuento') in self.env.user.permisos and self.env.ref('motgama.motgama_elimina_descuento') in self.env.user.permisos

    @api.multi
    def agregar_descuento(self):
        self.ensure_one()

        if self.valorDesc <= 0.0:
            return True
        
        valores = {
            'movimiento_id': self.habitacion.ultmovimiento.id,
            'habitacion_id': self.habitacion.id,
            'valorDesc': self.valorDesc,
            'usuario_id': self.env.user.id
        }
        nuevo = self.env['motgama.descuento'].sudo().create(valores)
        if not nuevo:
            raise Warning('No se pudo registrar el descuento')

        if self.habitacion.orden_venta:
            nuevo.sudo().aplica_descuento()
        
        return True

    @api.multi
    def editar_descuento(self):
        self.ensure_one()

        if self.valorDesc <= 0.0:
            raise Warning('No puede agregar este valor como descuento, si desea eliminarlo seleccione la operación "Eliminar"')

        desc = self.env['motgama.descuento'].search([('movimiento_id','=',self.habitacion.ultmovimiento.id)],limit=1)
        if not desc:
            raise Warning('No existe el descuento a modificar')

        if desc.valorDesc != self.valorDesc:
            desc.sudo().write({'valorDesc': self.valorDesc,'usuario_id': self.env.user.id})
            if desc.linea_id:
                desc.linea_id.sudo().write({'price_unit': 0.0 - self.valorDesc})

    @api.multi
    def eliminar_descuento(self):
        self.ensure_one()

        desc = self.env['motgama.descuento'].search([('movimiento_id','=',self.habitacion.ultmovimiento.id)],limit=1)
        if not desc:
            raise Warning('No existe el descuento a eliminar')

        if desc.linea_id:
            if desc.linea_id.order_id.state in ['sent','sale']:
                desc.linea_id.sudo().write({'product_uom_qty': 0,'price_unit': 0})
            elif desc.linea_id.order_id.state == 'draft':
                desc.linea_id.sudo().unlink()
            else:
                raise Warning('El estado de cuenta se encuentra en un estado desconocido y no se puede eliminar el descuento')
        desc.sudo().unlink()