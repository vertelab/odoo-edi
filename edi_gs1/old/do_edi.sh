#!/bin/bash

[ -f /tmp/do_edi-working ] && exit  # dont start another one

touch /tmp/do_edi-working
clean(){
    rm /tmp/do_edi-working
    exit
}
trap clean INT TERM EXIT ERR

DB=gv01
/usr/share/greenvision/do_import_order.py --database=$DB &
/usr/share/greenvision/do_ordrsp.py --database=$DB &
/usr/share/greenvision/do_dspadv.py --database=$DB &
/usr/share/greenvision/do_invoice.py --database=$DB 
wait
