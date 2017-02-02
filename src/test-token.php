<?php

define("MACKEY", "9bhaLHnw4g9@#");
define("TOKEN_TIMEOUT", 180); // sec

function validate_token($token) {
    if (!is_string($token)) return false;
    $ts = hexdec(substr($token, 0, 8));
    $nstones = hexdec(substr($token, 8, 8));
    $mac = substr($token, 16);
    
    if (!is_int($ts)) return false;
    if (!is_int($nstones)) return false;
    if (!is_string($mac)) return false;
    if ($ts < time() - TOKEN_TIMEOUT) return false;
    if (hash_hmac("sha1", "$ts|$nstones", MACKEY) !== $mac) return false;
    return array($ts, $nstones);
}

var_dump(validate_token($argv[1]));

?>