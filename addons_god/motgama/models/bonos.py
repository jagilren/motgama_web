from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaBonos(models.Model):
#    Fields: Bonos: el cliente tiene una forma de pago por medio de bonos Creado: Mayo 16 del 2019
    _name = 'motgama.bonos'
    _description = 'Bonos'
    _rec_name = 'codigo'
    _sql_constraints = [('codigo_uniq', 'unique (codigo)', "El Código ya Existe, Verifique!")]
    tipo_bono = fields.Selection(string='Tipo de bono',required=True,selection=[('unico','Bono único'),('consecutivo','Bonos consecutivos'),('multiple','Bono múltiple')],default='unico')
    prefijo = fields.Char(string='Prefijo',default='')
    cons_desde = fields.Integer(string='Consecutivo desde')
    cantidad = fields.Integer(string='Cantidad de bonos a generar')
    digitos = fields.Integer(string='Tamaño del consecutivo',help='Completará el código del bono con ceros a la izquierda para completar esa cantidad de dígitos, un cero significa que no tendrá ceros a la izquierda')
    codigo_inicial = fields.Char(string='Código inicial',compute='_compute_codigos',store=True)
    codigo_final = fields.Char(string='Código final',compute='_compute_codigos',store=True)
    codigo = fields.Char(string='Código')
    multiple = fields.Boolean(string='Múltiple',default=False)
    maximo_uso = fields.Integer(string='Cantidad máxima de usos (0 = ilimitado)', default=1)
    usos = fields.Integer(string='Usos hasta el momento',default=0)
    validodesde = fields.Date(string='Válido Desde',default=lambda self: fields.Date().today())
    validohasta = fields.Date(string='Válido Hasta',required=True)
    tipo = fields.Selection(string='Tipo de descuento',selection=[('valor','Valor en pesos'),('porcentaje','Valor porcentual')],default='porcentaje',required=True)
    descuentavalor = fields.Float(string='Valor de descuento',default=0.0)
    porcpagoefectivo = fields.Float(string='Porcentaje descuento',default=0.0)
    # El descuento se lo puede aplicar a :
    aplicahospedaje = fields.Boolean(string='Aplica en hospedaje',default=True)
    aplica_adicional = fields.Boolean(string="Aplica en hospedaje adicional",default=False)
    aplicarestaurante = fields.Boolean(string='Aplica en restaurante',default=False)
    aplicaconsumos = fields.Boolean(string='Aplica en otros productos',default=False)
    valor = fields.Float(string='Valor descuento',compute='_compute_valor')
    active = fields.Boolean(string='Activo',default=True)

    @api.onchange('aplicahospedaje')
    def _onchange_aplica(self):
        for record in self:
            if not record.aplicahospedaje:
                record.aplica_adicional = False

    @api.onchange('tipo_bono')
    def _onchange_tipobono(self):
        for record in self:
            if record.tipo_bono in ['unico','consecutivo']:
                record.multiple = False
            elif record.tipo_bono == 'multiple':
                record.multiple = True

    @api.onchange('multiple')
    def _onchange_multiple(self):
        for record in self:
            if not record.multiple:
                record.maximo_uso = 1
    
    @api.onchange('tipo')
    def _onchange_tipo(self):
        for record in self:
            if record.tipo == 'valor':
                record.porcpagoefectivo = 0.0
            elif record.tipo == 'porcentaje':
                record.descuentavalor = 0.0
    
    @api.depends('tipo','descuentavalor','porcpagoefectivo')
    def _compute_valor(self):
        for record in self:
            if record.tipo == 'valor':
                record.valor = record.descuentavalor
            elif record.tipo == 'porcentaje':
                record.valor = record.porcpagoefectivo

    @api.depends('prefijo','cons_desde','cantidad','digitos')
    def _compute_codigos(self):
        for record in self:
            if record.tipo_bono == 'consecutivo':
                if record.digitos <= 0:
                    cons_desde = str(record.cons_desde)
                    cons_hasta = str(record.cons_desde + record.cantidad - 1)
                elif record.digitos >= len(str(record.cons_desde + record.cantidad - 1)):
                    ceros = record.digitos - len(str(record.cons_desde))
                    cons_desde = ''
                    for x in range(ceros):
                        cons_desde += '0'
                    cons_desde += str(record.cons_desde)
                    ceros = record.digitos - len(str(record.cons_desde + record.cantidad - 1))
                    cons_hasta = ''
                    for x in range(ceros):
                        cons_hasta += '0'
                    cons_hasta += str(record.cons_desde + record.cantidad - 1)
                else:
                    raise Warning('No es posible cumplir con la cantidad de bonos requerida y el tamaño de consecutivo especificado')
                prefijo = record.prefijo if record.prefijo else ''
                record.codigo_inicial = prefijo + cons_desde
                record.codigo_final = prefijo + cons_hasta

    @api.model
    def create(self,values):
        prefijo = ''
        if 'prefijo' in values:
            if values['prefijo']:
                prefijo = values['prefijo']
        consecutivo = values['tipo_bono'] == 'consecutivo'
        if consecutivo:
            if values['cantidad'] <= 0:
                raise Warning('No es posible crear ' + str(values['cantidad']) + ' bonos')
            if values['digitos'] <= 0:
                values['codigo'] = prefijo + str(values['cons_desde'])
            elif values['digitos'] >= len(str(values['cons_desde'])):
                ceros = values['digitos'] - len(str(values['cons_desde']))
                values['codigo'] = prefijo
                for x in range(ceros):
                    values['codigo'] += '0'
                values['codigo'] += str(values['cons_desde'])
            else:
                raise Warning('No es posible cumplir con la cantidad de bonos requerida y el tamaño de consecutivo especificado')

        record = super().create(values)

        if consecutivo:
            valores = {
                'tipo_bono': 'unico',
                'multiple': False,
                'maximo_uso': 1,
                'usos': 0,
                'validodesde': record.validodesde,
                'validohasta': record.validohasta,
                'tipo': record.tipo,
                'descuentavalor': record.descuentavalor,
                'porcpagoefectivo': record.porcpagoefectivo,
                'aplicahospedaje': record.aplicahospedaje,
                'aplicarestaurante': record.aplicarestaurante,
                'aplicaconsumos': record.aplicaconsumos,
                'valor': record.valor,
                'active': True
            }
            for x in range(record.cons_desde + 1,record.cons_desde + record.cantidad):
                if record.digitos <= 0:
                    valores['codigo'] = prefijo + str(x)
                    bono = self.env['motgama.bonos'].create(valores)
                    if not bono:
                        raise Warning('No se pudo crear el bono ' + valores['codigo'])
                elif record.digitos >= len(str(x)):
                    ceros = record.digitos - len(str(x))
                    codigo = prefijo
                    for y in range(ceros):
                        codigo += '0'
                    valores['codigo'] = codigo + str(x)
                    bono = self.env['motgama.bonos'].create(valores)
                    if not bono:
                        raise Warning('No se pudo crear el bono ' + valores['codigo'])
                else:
                    raise Warning('No es posible cumplir con la cantidad de bonos requerida y el tamaño de consecutivo especificado')

        return record

    @api.multi
    def write(self,values):
        for x in values:
            if x in ['prefijo','cons_desde','cantidad','digitos']:
                raise Warning('No puede modificar los parámetros de los bonos consecutivos')
        return super().write(values)