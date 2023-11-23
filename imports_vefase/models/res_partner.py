from odoo import models, fields


class Patients(models.Model):
    _inherit = 'res.partner'

    international_type = fields.Boolean(string='Internacional', default=False)
