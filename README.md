# odoo-edi


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
 --- | ---
 account_invoice_credit_reason|
 edi_sale|
 sale_purchase|
 portal_edi|
 
 
