from odoo import models, fields, api
from odoo.exceptions import Warning

class MotgamaBonos(models.Model):
    _inherit = 'motgama.bonos'

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

class MotgamaFlujoHabitacion(models.Model):
    _inherit = 'motgama.flujohabitacion'

    bono_id = fields.Many2one(string="Bono",comodel_name='motgama.bonos')

    @api.multi
    def aplicar_bono(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_bono') in self.env.user.permisos:
            raise Warning('No tiene permitido agregar bonos, contacte al administrador')
        if self.ultmovimiento.bono_id:
            raise Warning('Ya se redimió un bono para esta habitación')

        return {
            'name': 'Aplicar bono',
            'type': 'ir.actions.act_window',
            'res_model': 'motgama.wizard.bono',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('motgama.wizard_bonos').id,
            'target': 'new'
        }

    @api.multi
    def quita_bono(self):
        self.ensure_one()
        if not self.env.ref('motgama.motgama_quita_bono') in self.env.user.permisos:
            raise Warning('No tiene permitido retirar bonos, contacte al administrador')

        self.ultmovimiento.sudo().write({'bono_id': False})
        self.bono_id.sudo().write({'usos': self.bono_id.usos - 1})
        self.sudo().write({'bono_id': False})

class MotgamaWizardBonos(models.TransientModel):
    _name = 'motgama.wizard.bono'
    _description = 'Wizard Bonos'

    habitacion = fields.Many2one(string='Habitación',comodel_name='motgama.flujohabitacion',default=lambda self: self._get_habitacion())
    codigo = fields.Char(string='Código del bono')
    inf_bono = fields.Many2many(string='Información del bono', comodel_name='motgama.bonos')
    bono_valido = fields.Boolean(string='Bono validado', default=False)
    bono = fields.Many2one(string='Bono',comodel_name='motgama.bonos')
    validar = fields.Boolean(string='Validar', default=False)

    @api.model
    def _get_habitacion(self):
        return self.env.context['active_id']

    @api.onchange('validar')
    def _onchange_validar(self):
        for record in self:
            if record.validar:
                bono = self.env['motgama.bonos'].sudo().search([('codigo','=',self.codigo)], limit=1)
                if not bono:
                    record.validar = False
                    raise Warning('El bono no existe o ha sido desactivado')

                if fields.Date().today() < bono.validodesde:
                    record.validar = False
                    raise Warning('El bono no está disponible todavía, es válido desde ' + str(bono.validodesde))
                elif fields.Date().today() > bono.validohasta:
                    record.validar = False
                    raise Warning('El bono se ha vencido, fue válido hasta ' + str(bono.validohasta))

                if bono.maximo_uso != 0 and bono.usos >= bono.maximo_uso:
                    record.validar = False
                    raise Warning('El bono ya cumplió su límite de usos, Cantidad máxima: ' + str(bono.maximo_uso))

                record.bono_valido = True
                record.inf_bono = [(6,0,[bono.id])]
                record.bono = bono.id

    @api.multi
    def agregar(self):
        self.ensure_one()

        self.habitacion.ultmovimiento.write({'bono_id': self.bono.id})
        self.habitacion.sudo().write({'bono_id': self.bono.id})
        self.bono.sudo().write({'usos': self.bono.usos + 1})
        return True