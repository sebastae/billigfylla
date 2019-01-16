<?php
    if(isset($_GET["id"])){
        if(($db = new SQLite3("./produkter.db")) !== false){
            $stmt = $db->prepare("SELECT * FROM Products WHERE Id = :Id");
            $stmt->bindValue(":Id", $_GET["id"], SQLITE3_INTEGER);

            $result = $stmt->execute();
            $data = $result->fetchArray();

            if($data !== false){
                ?>

                <p><b><a href="<?php echo $data["URL"]; ?>"><?php echo $data["Name"]; ?></a></b>[<?php echo $data["ProductNumber"]; ?>]: <?php echo $data["Volume"]; ?>L <?php echo $data["ProductType"]; ?>
                    &nbsp;(<?php echo $data["Alcohol"]; ?>%); Order Only: <?php echo $data["OrderOnly"] ? "true" : "false"; ?>
                </p>

                <?php
            } else {
                ?>
                <p>Den ID'en finnes ikke i databasen vår</p>
                <?php
            }

        } else {
            ?>
            <p>Beklager, vi kunne ikke nå databasen vår :(</p>
            <?php
        }
    } else {
        ?>
            <p>Ingen ID ble gitt</p>
    <?php
    }