<?php

$fp = $argv[1];
$request = fopen("verify{$fp}.xml", 'w');

$cont = <<<EOK
<?xml version="1.0" encoding="UTF-8"?>
<COMMAND>
<TYPE>TXNEQREQ</TYPE>
<EXTTRID>{$fp}</EXTTRID>
<MESSAGE>check</MESSAGE>
<language>2</language>
<TXNID></TXNID>
</COMMAND>
EOK;

fwrite($request, $cont);
fclose($request);
