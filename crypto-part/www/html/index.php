<?php

define("MACKEY", "9bhaLHnw4g9@#");
define("ADMIN_PASSWORD", "6c24263f37bf91f546efe71861d2e5255419574e");
define("TOKEN_TIMEOUT", 180); // sec
define("FLAG2", "SECCON{04d4869acf42d95509231a275e559522}");

if (!extension_loaded('pdo_sqlite')) {
    header("Content-type: text/plain");
    echo "PDO Driver for SQLite is not installed.";
    exit;
}
if (!extension_loaded('bcmath')) {
    header("Content-type: text/plain");
    echo "BC Math extension is not installed.";
    exit;
}
if (!extension_loaded('curl')) {
    header("Content-type: text/plain");
    echo "cURL extension is not installed.";
    exit;
}

function connect() {
    return new PDO("sqlite:../db/HoF.sqlite");
}

function create_table($db) {
    $db->exec("
CREATE TABLE hof (
id   INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
pk_n TEXT NOT NULL UNIQUE,
pk_e TEXT NOT NULL,
network TEXT NOT NULL,
ts   INTEGER NOT NULL,
time INTEGER NOT NULL,
nstones INTEGER NOT NULL,
deleted INTEGER NOT NULL DEFAULT 0
);
");
    $db->exec("CREATE INDEX hof_network_ts ON hof(network, ts);");
    $db->exec("CREATE INDEX hof_network ON hof(network, deleted);");
    $db->exec("CREATE INDEX hof_search ON hof(deleted, nstones, time);");
}

function to_network($ip) {
    // 本番ネットワーク構成を元にチームのネットワークアドレスに変換
    $ip = preg_replace('/\\.\\d+$/', '.0', $ip);
    return $ip;
}

function proof_of_work($ts, $input) {
    $d = sha1("$ts|$input");
    return substr($d, 0, 5) === "00000" &&
        in_array(substr($d, 5, 1), array("0", "1", "2", "3"));
}

function verify($m, $sig, $n, $e) {
    $m1 = bcmod($m, $n);
    $m2 = bcpowmod($sig, $e, $n);
    return $m1 === $m2;
}

function byte_to_int($s) {
    $x = 0;
    foreach (str_split($s) as $c) {
        $x = bcadd(bcmul($x, 256), ord($c));
    }
    return $x;
}

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

function validate_name($name) {
    if (!is_string($name)) return false;
    if (strlen($name) > 128) return false;
    return true;
}
function validate_pk($n, $e) {
    if (!is_string($n)) return false;
    if (!is_string($e)) return false;
    if (!preg_match('/^[1-9][0-9]{0,49}$/', $n)) return false;
    if (!preg_match('/^[1-9][0-9]{0,49}$/', $e)) return false;
    return true;
    
}

function respond_error($reason) {
    $a = array("status" => "error", "reason" => $reason);
    echo json_encode($a);
    exit;
}

function respond_ok($misc = null) {
    $a = array("status" => "ok");
    if (is_array($misc)) {
        $a = array_merge($a, $misc);
    }
    echo json_encode($a);
    exit;
}

function register($name, $ts, $nstones, $sig, $n, $e, $ip) {
    if (!validate_name($name) || !validate_pk($n, $e)) {
        respond_error("invalid input");
    }
    $ts = (int)$ts;
    $nstones = (int)$nstones;
    $sigm = bcadd(bcmul(byte_to_int($name), "4294967296"), $ts & 0xffffffff);
    if (!verify($sigm, $sig, $n, $e)) {
        respond_error("invalid signature for ($n, $e)");
    }

    $db = connect();
    $network = to_network($ip);
    $stmt = $db->prepare("SELECT COUNT(*) FROM hof WHERE network=? AND NOT deleted");
    $stmt->bindParam(1, $network, PDO::PARAM_STR);
    $stmt->execute();
    if ($stmt->fetchColumn() > 10) {
        respond_error("too many registerations from your network");
    }

    $stmt = $db->prepare("SELECT COUNT(*) FROM hof WHERE network=? AND ts=?");
    $stmt->bindParam(1, $network, PDO::PARAM_STR);
    $stmt->bindValue(2, $ts, PDO::PARAM_INT);
    $stmt->execute();
    if ($stmt->fetchColumn() != 0) {
        respond_error("already registered with the token");
    }

    $stmt = $db->prepare("INSERT INTO hof (name, pk_n, pk_e, network, ts, time, nstones) VALUES (?, ?, ?, ?, ?, ?, ?)");
    $stmt->bindParam(1, $name, PDO::PARAM_STR);
    $stmt->bindParam(2, $n, PDO::PARAM_STR);
    $stmt->bindParam(3, $e, PDO::PARAM_STR);
    $stmt->bindParam(4, $network, PDO::PARAM_STR);
    $stmt->bindValue(5, $ts, PDO::PARAM_INT);
    $stmt->bindValue(6, (int)time(), PDO::PARAM_INT);
    $stmt->bindValue(7, $nstones, PDO::PARAM_INT);
    if (!$stmt->execute()) {
        respond_error("already registered with the pk_n");
    }
    $id = $db->lastInsertId();
    respond_ok(array("id" => $id));
}

function unregister($id, $sig, $ip) {
    $flag = null;
    
    $db = connect();
    $stmt = $db->prepare("SELECT pk_n, pk_e, network FROM hof WHERE id = ? AND NOT deleted");
    $stmt->bindValue(1, $id, PDO::PARAM_INT);
    $stmt->execute();
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($result === False) {
        respond_error("no record");
    }
    $n = $result["pk_n"];
    $e = $result["pk_e"];
    $network = $result["network"];

    $other_team = ($network != to_network($ip));
    
    $sigm = bcadd(bcmul(byte_to_int("delete"), "4294967296"), $id & 0xffffffff);
    if (!verify($sigm, $sig, $n, $e)) {
        respond_error("invalid signature for ($n, $e)");
    }
    
    $stmt = $db->prepare("UPDATE hof SET deleted=1 WHERE id = ?");
    $stmt->bindValue(1, $id, PDO::PARAM_INT);
    $stmt->execute();
    if ($other_team) {
        $flag = FLAG2;
    }
    respond_ok(array("flag" => $flag));
}

function alice($db) {
    # Alice
    $name = "Alice";
    $n = trim(`python ../genkey.py`);
    $e = "65537";
    $network = "0.0.0.0";
    $ts = 0;
    $nstones = 127;

    $stmt = $db->prepare("INSERT INTO hof (name, pk_n, pk_e, network, ts, time, nstones) VALUES (?, ?, ?, ?, ?, ?, ?)");
    $stmt->bindParam(1, $name, PDO::PARAM_STR);
    $stmt->bindParam(2, $n, PDO::PARAM_STR);
    $stmt->bindParam(3, $e, PDO::PARAM_STR);
    $stmt->bindParam(4, $network, PDO::PARAM_STR);
    $stmt->bindValue(5, $ts, PDO::PARAM_INT);
    $stmt->bindValue(6, (int)time(), PDO::PARAM_INT);
    $stmt->bindValue(7, $nstones, PDO::PARAM_INT);
    $stmt->execute();
}

function admin_clear($password) {
    if ($password !== ADMIN_PASSWORD) {
        exit;
    }
    $db = connect();
    $stmt = $db->prepare("UPDATE hof SET deleted=1 WHERE deleted=0");
    $stmt->execute();

    alice($db);
    
    respond_ok();
}

function admin_reset($password) {
    if ($password !== ADMIN_PASSWORD) {
        exit;
    }
    $db = connect();
    
    $stmt = $db->prepare("DROP TABLE IF EXISTS hof");
    $stmt->execute();

    create_table($db);

    respond_ok();
}

function h($s) { return htmlspecialchars($s, ENT_QUOTES, "utf-8"); }

function show($exclude_newbies, $all=false) {
    $cond_sql = "";
    if ($exclude_newbies) {
        $cond_sql = "AND time <= " . (time() - (int)$exclude_newbies);
    }
    
    $db = connect();
    $result = $db->query("SELECT nstones FROM hof WHERE NOT deleted $cond_sql ORDER BY nstones LIMIT 1");
    $nstones = $result->fetchColumn();
    
    header("content-type", "text/html; charset=utf-8");
    print "<!DOCTYPE html>\n";
    print "<head>\n";
    print "<title>Hall of Fame</title>\n";
    print "</head>\n";
    print "<body>\n";
    print "<h1>Hall of Fame</h1>\n";
    print "<p>\n";
    print "<a href=\"http://go.1.finals.seccon.jp/files/AI\">He</a> is a last year's winner.\n";
    print "<a href=\"http://go.1.finals.seccon.jp/\">Play Go</a> and defeat him!\n";
    print "</p>\n";
    print "<table border>\n";
    print "<tr><th>#stones</th><th>name</th><th>at</th></tr>\n";
    if ($nstones !== false) {
        if (!$all) {
            $cond_sql .= " AND nstones=$nstones";
        }
        $result = $db->query("SELECT name, nstones, time FROM hof WHERE NOT deleted $cond_sql ORDER BY id");
        
        foreach ($result as $row) {
            print "<tr><td>";
            print h($row["nstones"]);
            print "</td><td>";
            print h($row["name"]);
            print "</td><td>";
            print h(date(DATE_RFC2822, $row["time"]));
            print "</td></tr>\n";
        }
    }
    print "</table>\n";
    if (!$all) {
        $allurl = $_SERVER["REQUEST_URI"];
        if (strpos($allurl, '?') !== false) {
            $allurl .= '&all=1';
        } else {
            $allurl .= '?all=1';
        }
        print "<a href=\"" . h($allurl) . "\">more</a>\n";
    }
    print "</body>\n";
    print "</html>\n";
}

if (!isset($_GET["cmd"])) {
    if (isset($_GET["exclude_newbies"])) {
        $exclude_newbies = $_GET["exclude_newbies"];
    }
    else {
        $exclude_newbies = 0;
    }
    if (isset($_GET["all"])) {
        $all = !!$_GET["all"];
    }
    else {
        $all = false;
    }
    show($exclude_newbies, $all);
}
else if ($_GET["cmd"] == "register") {
    if (isset($_GET["token"]) && isset($_GET["proof_of_work"]) && isset($_GET["name"]) && isset($_GET["sig"]) && isset($_GET["n"]) && isset($_GET["e"])) {
        $token = $_GET["token"];
        $token_result = validate_token($token);
        if ($token_result === false) {
            respond_error("invalid or timeout token");
        }
        list($ts, $nstones) = $token_result;
        if (!proof_of_work($ts, $_GET["proof_of_work"])) {
            respond_error("invalid proof-of-work");
        }
        register($_GET["name"], $ts, $nstones, $_GET["sig"], $_GET["n"], $_GET["e"], $_SERVER["REMOTE_ADDR"]);
    }
}
else if ($_GET["cmd"] == "unregister") {
    if (isset($_GET["id"]) && isset($_GET["sig"])) {
        unregister($_GET["id"], $_GET["sig"], $_SERVER["REMOTE_ADDR"]);
    }
}
else if ($_GET["cmd"] == "admin_clear") {
    if (isset($_GET["password"])) {
        admin_clear($_GET["password"]);
    }
}
else if ($_GET["cmd"] == "admin_reset_dangerous") {
    if (isset($_GET["password"])) {
        admin_reset($_GET["password"]);
    }
}


?>
