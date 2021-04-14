from odoo import models, fields, api

class MotgamaRecepcion(models.Model):#ok
#    Fields: RECEPCION: Aca estaran las diferentes recepciones por lo general sera RECEPCION A y RECEPCION B.
    _name = 'motgama.recepcion'
    _description = u'Recepción'
    _rec_name = 'nombre'
    _order = 'nombre ASC'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    sucursal_id = fields.Many2one(string=u'Sucursal',comodel_name='motgama.sucursal',ondelete='set null',)
    codigo = fields.Char(string=u'Código',) 
    nombre = fields.Char(string=u'Nombre de recepción',required=True)
    active = fields.Boolean(string=u'Activo?',default=True)
    zonas_ids = fields.One2many(string=u'Zonas en esta recepción',comodel_name='motgama.zona',inverse_name='recepcion_id') #LAS ZONAS EN ESTA RECEPCION
    canal_id = fields.Many2one(string='Canal',comodel_name='mail.channel')

    @api.model
    def create(self,values):
        record = super().create(values)

        parent = self.env['stock.location'].sudo().search([('name','=','MOTGAMA')],limit=1)
        if not parent:
            valores = {
                'name' : 'MOTGAMA',
                'usage' : 'internal',
                'permite_consumo' : False
            }
            parent = self.env['stock.location'].sudo().create(valores)
            if not parent:
                raise Warning('No existe ni se pudo crear el lugar de inventario "MOTGAMA", contacte al administrador')

        valoresLugar = {
            'name' : record.nombre,
            'recepcion' : record.id,
            'usage' : 'internal',
            'location_id' : parent.id,
            'permite_consumo' : True
        }
        nuevoLugar = self.env['stock.location'].sudo().create(valoresLugar)
        if not nuevoLugar:
            raise Warning('Error al crear recepción: No se pudo crear el lugar de inventario para la nueva recepción')

        return record
    
    @api.multi
    def write(self,values):
        creado = super(MotgamaRecepcion, self).write(values)

        lugar = self.env['stock.location'].sudo().search([('recepcion','=',self.id)],limit=1)
        if not lugar:
            parent = self.env['stock.location'].sudo().search([('name','=','MOTGAMA')],limit=1)
            if not parent:
                valores = {
                    'name' : 'MOTGAMA',
                    'usage' : 'internal',
                    'permite_consumo' : False
                }
                parent = self.env['stock.location'].sudo().create(valores)
                if not parent:
                    raise Warning('No existe ni se pudo crear el lugar de inventario "MOTGAMA", contacte al administrador')

            valoresLugar = {
                'name' : self.nombre,
                'recepcion' : self.id,
                'usage' : 'internal',
                'location_id' : parent.id,
                'permite_consumo' : True
            }
            lugar = self.env['stock.location'].sudo().create(valoresLugar)
            if not lugar:
                raise Warning('Error al crear el lugar de inventario para la recepción')
        else:
            lugar.write({'name':self.nombre})
        
        return creado