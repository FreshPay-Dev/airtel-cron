<?php
$fp = $argv[1];
$commmand = "curl -k -H \"text/xml\" --data @req{$fp}.xml -X POST 'https://172.26.35.213:5577/FRESHPAY?LOGIN=FRESHPAY&PASSWORD=9500ad5830a85138808d7328ce0c460c'";
$out = shell_exec($commmand);
$handle = fopen("responseB2C{$fp}.xml", 'w');
fwrite($handle, $out);
fclose($handle);
