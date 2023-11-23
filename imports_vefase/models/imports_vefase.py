from odoo import models, fields, api


class ImportsVefase(models.Model):
    _name = 'imports.vefase'
    _description = 'Importaciones Vefase'
    _rec_name = 'bl_code'

    bl_code = fields.Char(string='Numero de Control', required=True)
    description = fields.Text(string='Description')
    stage = fields.Selection([
        ('new', 'Nuevo'),
        ('in_process', 'En Proceso'),
        ('complete', 'Completado'),
        ('cancel', 'Cancelado')
    ], string='Estatus', group_expand='_expand_stages', default='new')
    priority = fields.Selection([
        ('0', 'Ninguna'),
        ('1', 'Baja'),
        ('2', 'Media'),
        ('3', 'Alta'),
    ], 'Prioridad', default='0')
    partner_id = fields.Many2one(
                'res.partner',
                string='Proveedor',
                domain=[('international_type', '=', True)],
                help='Selecione una Empresa de tipo Internacional'
    )
    country_id = fields.Many2one('res.country', string='Pais de Origen')
    origin_city = fields.Char(string='Ciudad de Origen')
    destiny_country_id = fields.Many2one('res.country', string='Pais de Destino')
    destiny_city = fields.Char(string='Ciudad de Destino')
    loading_port = fields.Many2one('loading.unloading', string='Puerto de Carga')
    discharge_port = fields.Many2one('loading.unloading', string='Puerto de Descarga')
    current_location = fields.Char(string='Ubicacion Actual')
    import_type = fields.Selection(
                [('null', ''), ('maritimo', 'Marítimo'), ('aereo', 'Aéreo')],
                string='Medio de Importación',
                required=True,
                default='null',
                help='Seleccione el tipo de importación: marítimo o aéreo'
    )
    aereal_id = fields.Many2one('company.aereal', string='Compañía Responsable')
    nautical_id = fields.Many2one('company.nautical', string='Compañía Responsable')
    estimated_date = fields.Date(string='Fecha de Llegada')
    limit_pay_date = fields.Date(string='Fecha Limite de Pago')
    balance = fields.Float(string='Saldo', compute='_compute_total_balance')
    delivery_date = fields.Date(string='Fecha de Entrega')
    delivery_number = fields.Char(string='Numero de Guia')
    container_ids = fields.One2many('imports.vefase.lines', 'container_id', string='Nombre')
    notes = fields.Html(string="Notas")
    checklist_ids = fields.One2many('check.list.lines', 'container_id')
    todo_check = fields.Char(string="Tareas Pendiente", compute="_compute_todo")
    todo_name = fields.Char(string="Ultima Tarea", compute="_compute_todo_name")

    def _expand_stages(self, states, domain, order):
        # return all stages
        return [key for key, val in type(self).stage.selection]

    @api.depends('checklist_ids.status')
    def _compute_todo(self):
        for rec in self:
            lines = rec.checklist_ids.filtered(lambda r: not r.status)
            if not rec.checklist_ids:
                rec.todo_check = 'No hay tareas pendientes'
            elif not lines:
                rec.todo_check = 'Se han realizado todas las tareas'
            elif len(lines) == 1:
                rec.todo_check = 'Hay 1 tarea pendiente'
            else:
                rec.todo_check = f'Hay {len(lines)} tareas pendientes'

    @api.depends('checklist_ids.checklist_id.name')
    def _compute_todo_name(self):
        for rec in self:
            lines = rec.checklist_ids.filtered(lambda r: not r.status)
            if not lines:
                rec.todo_name = False
            else:
                rec.todo_name = lines[-1].checklist_id.name

    @api.depends('container_ids')
    def _compute_total_balance(self):
        balance = 0
        for rec in self.container_ids:
            balance += rec.total_price + rec.total_fiscal + rec.total_financial
        self.balance = balance


class ImportsLines(models.Model):
    _name = 'imports.vefase.lines'
    _description = 'Contenedores de la Importacion'
    _rec_name = 'container_id'

    containers_id = fields.Many2one('container.lines', string='Contenedor',
                                    domain=[('status', '=', False)])
    container_id = fields.Many2one('imports.vefase')
    total_price = fields.Float(related='containers_id.total_price')
    total_currency = fields.Float(related='containers_id.total_currency')
    total_financial = fields.Float(related='containers_id.total_price_financial')
    total_fiscal = fields.Float(related='containers_id.total_price_fiscal')
    total_financial_rate = fields.Float(related='containers_id.total_currency_financial')
    total_fiscal_rate = fields.Float(related='containers_id.total_currency_fiscal')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.containers_id:
            record.containers_id.write({'status': True})
        return record

    def unlink(self):
        for record in self:
            if record.containers_id:
                record.containers_id.write({'status': False})
        return super().unlink()

class ChecklistLines(models.Model):
    _name = 'check.list.lines'
    _description = 'Checklist de la Improtacion'
    _rec_name = 'checklist_id'

    checklist_id = fields.Many2one('check.list', string='Checklist')
    container_id = fields.Many2one('imports.vefase')
    status = fields.Boolean("Estatus")
