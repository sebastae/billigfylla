
<?php

    require_once './vendor/autoload.php';

    $loader = new Twig_Loader_Filesystem('./templates');
    $twig = new Twig_Environment($loader, array(
            // Options
    ));

    $maxprice = isset($_GET["mp"]) ? $_GET["mp"] : 250;
    $minvolume = isset($_GET["mnv"]) ? $_GET["mnv"] : 0;
    $maxvolume = isset($_GET["mxv"]) ? $_GET["mxv"] : false;
    $orderonly = isset($_GET["o"]) ? 1 : 0;
    $includeStr = isset($_GET["include"]) ? $_GET["include"] : false;


    if ($includeStr !== false){
        $words = explode(" ",$includeStr);

        function mp($w){
            return sprintf("%08d", decbin(intval($w,36)));
        }

        $words = array_map(mp,$words);

        function concat($a, $b){
            return $a . $b;
        }

        $binStr = array_reduce($words,concat);

        $includeArray = str_split($binStr);
    }


    if(($db = new SQLite3("./produkter.db")) !== false) {

        $maxvolume_query = "";
        if($maxvolume !== false){
            $maxvolume_query = "AND Volume <= :Maxvolume";
        }

        $stmt = $db->prepare("SELECT * FROM Products WHERE  OrderOnly = 0 AND Alcohol > 0 AND Price <= :Maxprice AND Volume >= :Minvolume ORDER BY Ranking DESC LIMIT 50");
        $stmt->bindValue(':Maxprice', $maxprice);
        $stmt->bindValue(":Minvolume", $minvolume);
        if($maxvolume !== false) {
            $stmt->bindValue(":Maxvolume", $minvolume);
        }
        $stmt->bindValue(':OrderOnly', 1);

        $result = $stmt->execute();
    }

    $r = array();
    while (($data = $result->fetchArray(SQLITE3_ASSOC)) !== false){
        array_push($r, $data);
    }

    $types = array();
    $stmt = $db->prepare("SELECT * FROM ProductTypes");
    $result = $stmt->execute();

    while (($data = $result->fetchArray(SQLITE3_ASSOC)) !== false){
        array_push($types, array(
            'name' => $data["Type"],
            'selected' => isset($includeArray) ? boolval($includeArray[$data["Id"]]) : true,
            'id' => $data["Id"]
        ));
    }


    $stmt = $db->prepare("SELECT Price FROM Products ORDER BY Price DESC LIMIT 1");
    $result = $stmt->execute();

    $template = $twig->load('base.html.twig');
    echo $template->render(array(
        'products' => $r,
        'maxprice' => $maxprice,
        'minvolume' => $minvolume,
        'maxvolume' => $maxvolume,
        'types' => $types

    ));
