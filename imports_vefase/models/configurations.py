from odoo import models, fields


class CompanyAereal(models.Model):
    _name = 'company.aereal'
    _description = 'Compañía Aerea'
    _rec_name = 'name'

    name = fields.Char(string='Nombre', required=True)


class CompanyNautical(models.Model):
    _name = 'company.nautical'
    _description = 'Compañía Maritima'
    _rec_name = 'name'

    name = fields.Char(string='Nombre', required=True)


class SizeParameter(models.Model):
    _name = 'size.parameter'
    _description = 'Medidas de la Carga'
    _rec_name = 'size'

    size = fields.Char(string='Medida', required=True)


class Checklist(models.Model):
    _name = 'check.list'
    _description = 'Checklist'
    _rec_name = 'name'

    name = fields.Char(string='Nombre', required=True)


class FiscalExpenses(models.Model):
    _name = 'fiscal.expenses'
    _description = 'Gastos Fiscales'
    _rec_name = 'name'

    name = fields.Char(string='Nombre', required=True)
    account_ids = fields.Many2one('account.account', string='Cuenta Asociada')


class FinancialExpenses(models.Model):
    _name = 'financial.expenses'
    _description = 'Gastos Financieros'
    _rec_name = 'name'

    name = fields.Char(string='Nombre', required=True)
    account_ids = fields.Many2one('account.account', string='Cuenta Asociada')


class LoadingUnloading(models.Model):
    _name = 'loading.unloading'
    _description = 'Puertos de Carga y Descarga'
    _rec_name = 'dock_name'

    dock_name = fields.Char(string='Nombre', required=True)
