# odoo-edi

account_invoice_credit_reason  edi_peppol          edi_route_sale_stock
edi_gs1                        edi_route           edi_route_stock
edi_gs1_axfood                 edi_route_ftp       edi_sale
edi_gs1_coop                   edi_route_mail      portal_edi
edi_gs1_ica                    edi_route_purchase  README.md
edi_gs1_product_customer_code  edi_route_sale      sale_purchase

EDI-modules |Description
--- | --- 
 edi_route                 | Main module for communication services and routing. Adds generic routes, envelopes and messages for EDI usage
 edi_route_ftp| Sftp and FTP communication server. Requires python libraries paramiko and pycrypto
 edi_route_mail | Mail communation server, ties an email address to a route
 edi_route_[purchase,sale,sale_stock,stock]| Catches and ties signals to routing
 edi_gs1| Implements GS1 and EDIFACT. ESAP20-routing
 edi_gs1_[ica,axfood,coop,bergendahls]| Implements special handling of these parties
 edi_peppol| Implements PEPPOL
 
 Other modules |Description
 account_invoice_credit_reason|
 edi_sale|k
 sale_purchase|k
 
 
