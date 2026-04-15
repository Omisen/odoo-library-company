from odoo import models, fields

class LibraryCategory(models.Model):
    _name = "library.category"
    _description = "Library Category"
    
    name = fields.Char(required=True)
    description = fields.Char()