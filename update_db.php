<?php
    $dbfile = "./produkter.db";
    $dbTable = "Products";

    // File gotten from https://www.vinmonopolet.no/datadeling
    $productfile = "./produkter.csv";
    if(($productCsv = fopen("$productfile", "r")) !== false) {

        $nameCol = 2;
        $productNumCol = 1;
        $volumeCol = 3;
        $priceCol = 4;
        $volumePriceCol = 5;
        $productTypeCol = 6;
        $productAvailabilityCol = 7;
        $alcoholCol = 26;
        $urlCol = 35;


        $head = fgets($productCsv);


        $id = 0;
        if(($productDb = new SQLite3($dbfile)) !== false){
            $stime = new DateTime();
            $productDb->exec("DELETE FROM $dbTable WHERE Id > 0");
            while(($product = explode(";",utf8_encode(fgets($productCsv)))) !== false and count($product) > 1){

                $name = $product[$nameCol];
                $productNumber = intval($product[$productNumCol]);
                $productType = $product[$productTypeCol];
                $volume = floatval(str_replace(',','.',$product[$volumeCol]));
                $price = floatval($product[$priceCol]);
                $volumePrice = floatval($product[$volumePriceCol]);
                $alcohol = floatval($product[$alcoholCol]);
                $productAvailability = $product[$productAvailabilityCol];
                $url = $product[$urlCol];

                if($alcohol > 0) {
                    $alcoholPrice = $price / $alcohol;
                } else {
                    $alcoholPrice = 0;
                }
                // Check if product is order-only
                $orderOnly = $productAvailability === "Bestillingsutvalget" ? 1 : 0;

                // Only include product if it is a drink, i.e has volume
                if($volume != 0) {
                    $query = $productDb->prepare("INSERT INTO $dbTable VALUES(:Id,:Name,:ProductNumber,:ProductType,:Volume,:Price,:VolumePrice,:Alcohol,:AlcoholPrice,:OrderOnly,:URL)");
                    $query->bindValue(":Id", ++$id, SQLITE3_INTEGER);
                    $query->bindValue(":Name", $name, SQLITE3_TEXT);
                    $query->bindValue(":ProductNumber", $productNumber, SQLITE3_INTEGER);
                    $query->bindValue(":ProductType", $productType, SQLITE3_TEXT);
                    $query->bindValue(":Volume", $volume, SQLITE3_FLOAT);
                    $query->bindValue(":Price", $price, SQLITE3_FLOAT);
                    $query->bindValue(":VolumePrice", $volumePrice, SQLITE3_FLOAT);
                    $query->bindValue(":Alcohol", $alcohol, SQLITE3_FLOAT);
                    $query->bindValue(":AlcoholPrice", $alcoholPrice, SQLITE3_FLOAT);
                    $query->bindValue(":OrderOnly", $orderOnly, SQLITE3_INTEGER);
                    $query->bindValue(":URL", $url, SQLITE3_TEXT);

                    $result = $query->execute();
                    //echo "<p>INSERT ID $id : $productNumber ($volume) $name</p>";
                }

            }
            $productDb->close();
            $etime = new DateTime();
            $diff = $etime->diff($stime)->s;
            echo "Done in $diff seconds";
        }

    }