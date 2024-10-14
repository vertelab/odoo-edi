# -*- coding: utf-8 -*-
# from odoo import http


# class ScaffoldTest(http.Controller):
#     @http.route('/scaffold_test/scaffold_test/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/scaffold_test/scaffold_test/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('scaffold_test.listing', {
#             'root': '/scaffold_test/scaffold_test',
#             'objects': http.request.env['scaffold_test.scaffold_test'].search([]),
#         })

#     @http.route('/scaffold_test/scaffold_test/objects/<model("scaffold_test.scaffold_test"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('scaffold_test.object', {
#             'object': obj
#         })
