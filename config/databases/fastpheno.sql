-- MySQL dump 10.13  Distrib 8.4.2, for Linux (x86_64)
--
-- Host: localhost    Database: fastpheno
-- ------------------------------------------------------
-- Server version	8.4.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `fastpheno`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `fastpheno` /*!40100 DEFAULT CHARACTER SET utf8mb4 */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `fastpheno`;

--
-- Table structure for table `sites`
--

DROP TABLE IF EXISTS `sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sites` (
  `sites_pk` int NOT NULL AUTO_INCREMENT,
  `site_name` varchar(45) NOT NULL,
  `lat` decimal(15,12) NOT NULL,
  `lng` decimal(15,12) NOT NULL,
  `site_desc` varchar(999) DEFAULT NULL,
  PRIMARY KEY (`sites_pk`),
  UNIQUE KEY `site_name` (`site_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sites`
--

LOCK TABLES `sites` WRITE;
/*!40000 ALTER TABLE `sites` DISABLE KEYS */;
INSERT INTO `sites` VALUES (1,'Pintendre',46.740374307111,-71.134103487947,'Pintendre site'),(2,'Pickering',43.976084584507,-79.155886757746,'Pickering site');
/*!40000 ALTER TABLE `sites` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flights`
--

DROP TABLE IF EXISTS `flights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flights` (
  `flights_pk` int NOT NULL AUTO_INCREMENT,
  `pilot` varchar(45) DEFAULT NULL,
  `flight_date` datetime NOT NULL,
  `sites_pk` int NOT NULL,
  `height` decimal(15,10) DEFAULT NULL,
  `speed` decimal(15,10) DEFAULT NULL,
  PRIMARY KEY (`flights_pk`),
  KEY `flights_sites_fk_idx` (`sites_pk`),
  CONSTRAINT `flights_sites_fk` FOREIGN KEY (`sites_pk`) REFERENCES `sites` (`sites_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flights`
--

LOCK TABLES `flights` WRITE;
/*!40000 ALTER TABLE `flights` DISABLE KEYS */;
INSERT INTO `flights` VALUES (14,NULL,'2022-06-10 00:00:00',1,NULL,NULL),(15,NULL,'2022-07-16 00:00:00',1,NULL,NULL);
/*!40000 ALTER TABLE `flights` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trees`
--

DROP TABLE IF EXISTS `trees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trees` (
  `trees_pk` int NOT NULL AUTO_INCREMENT,
  `sites_pk` int NOT NULL,
  `longitude` decimal(15,12) NOT NULL,
  `latitude` decimal(15,12) NOT NULL,
  `tree_site_id` varchar(45) DEFAULT NULL,
  `family_id` varchar(45) DEFAULT NULL,
  `external_link` varchar(200) DEFAULT NULL,
  `block_num` int(4) DEFAULT NULL,
  `seq_id` varchar(25) DEFAULT NULL,
  `x_pos` int(10) DEFAULT NULL,
  `y_pos` int(10) DEFAULT NULL,
  `height_2022` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`trees_pk`),
  KEY `trees_sites_fk_idx` (`sites_pk`),
  CONSTRAINT `trees_sites_fk` FOREIGN KEY (`sites_pk`) REFERENCES `sites` (`sites_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trees`
--

LOCK TABLES `trees` WRITE;
/*!40000 ALTER TABLE `trees` DISABLE KEYS */;
INSERT INTO `trees` VALUES
(1,1,-71.134606710951,46.740492838807,'c',NULL,NULL,6,'PIN_2547',38,68,'-1'),
(2,1,-71.134693444446,46.739706272423,'127.07',NULL,NULL,5,'PIN_1301',9,35,'210'),
(3,1,-71.133814526723,46.740219868520,'619.03',NULL,NULL,6,'PIN_2970',6,79,'273'),
(4,1,-71.133710686130,46.740917414015,'1217.06',NULL,NULL,7,'PIN_4135',31,109,'300'),
(5,1,-71.135473011332,46.739610902839,'2346.11',NULL,NULL,5,'PIN_355',26,10,'335'),
(6,1,-71.135569085909,46.739395807101,NULL,NULL,NULL,NULL,'PIN_6232',20,-1,NULL),
(7,1,-71.133666755146,46.740193293865,'c',NULL,NULL,6,'PIN_3116',1,82,'-1'),
(8,1,-71.133225418530,46.741142099373,'1756.12',NULL,NULL,7,'PIN_4967',27,131,'371'),
(9,1,-71.135196603859,46.739519816924,'1883.04',NULL,NULL,5,'PIN_518',15,14,'320'),
(10,1,-71.134888423241,46.740253827983,'2349.01',NULL,NULL,5,'PIN_1936',36,51,'358'),
(2260,1,-71.133110604530,46.741369741463,'619.02',NULL,NULL,7,'PIN_2260',33,143,'300'),
(5384,1,-71.134685695396,46.740188723522,'619.12',NULL,NULL,7,'PIN_2025',28,54,'410');
/*!40000 ALTER TABLE `trees` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trees_flights_join_tbl`
--

DROP TABLE IF EXISTS `trees_flights_join_tbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trees_flights_join_tbl` (
  `trees_pk` int NOT NULL,
  `flights_pk` int NOT NULL,
  `confidence` decimal(8,5) DEFAULT NULL,
  PRIMARY KEY (`trees_pk`,`flights_pk`),
  KEY `tfjt_flights_fk_idx` (`flights_pk`),
  CONSTRAINT `tfjt_trees_fk` FOREIGN KEY (`trees_pk`) REFERENCES `trees` (`trees_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `tfjt_flights_fk` FOREIGN KEY (`flights_pk`) REFERENCES `flights` (`flights_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trees_flights_join_tbl`
--

LOCK TABLES `trees_flights_join_tbl` WRITE;
/*!40000 ALTER TABLE `trees_flights_join_tbl` DISABLE KEYS */;
INSERT INTO `trees_flights_join_tbl` VALUES (1,14,0.99769),(1,15,0.99823),(2,14,0.99831),(3,14,0.99856),(2260,14,0.99654),(5384,14,0.99840);
/*!40000 ALTER TABLE `trees_flights_join_tbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bands`
--

DROP TABLE IF EXISTS `bands`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bands` (
  `trees_pk` int NOT NULL,
  `flights_pk` int NOT NULL,
  `band` varchar(20) NOT NULL,
  `value` decimal(8,5) NOT NULL,
  PRIMARY KEY (`trees_pk`,`flights_pk`,`band`),
  KEY `bands_flight_band_tree_idx` (`flights_pk`,`band`,`trees_pk`),
  CONSTRAINT `bands_tfjt_fk` FOREIGN KEY (`trees_pk`,`flights_pk`) REFERENCES `trees_flights_join_tbl` (`trees_pk`,`flights_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bands`
--

LOCK TABLES `bands` WRITE;
/*!40000 ALTER TABLE `bands` DISABLE KEYS */;
INSERT INTO `bands` VALUES
(1,14,'1002nm',1.52376),(1,14,'398nm',0.07344),(1,14,'400nm',0.07803),(1,14,'402nm',0.07608),
(1,14,'405nm',0.08176),(1,14,'407nm',0.07852),(1,14,'409nm',0.18621),(1,14,'411nm',0.07256),
(1,14,'414nm',0.08194),(1,14,'416nm',0.07675),
(1,15,'1002nm',0.81632),(1,15,'398nm',0.04504),(1,15,'400nm',0.04862),(1,15,'402nm',0.05335),
(1,15,'405nm',0.05336),(1,15,'407nm',0.05417),(1,15,'409nm',0.10724),(1,15,'411nm',0.04718),
(1,15,'414nm',0.05260),(1,15,'416nm',0.04857),
(2,14,'398nm',0.03096),(3,14,'398nm',0.03606),
(2260,14,'398nm',0.03531),(5384,14,'398nm',0.03913);
/*!40000 ALTER TABLE `bands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pigments`
--

DROP TABLE IF EXISTS `pigments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pigments` (
  `trees_pk` int NOT NULL,
  `flights_pk` int NOT NULL,
  `pigment` int NOT NULL,
  `value` decimal(20,15) NOT NULL,
  PRIMARY KEY (`trees_pk`,`flights_pk`,`pigment`),
  CONSTRAINT `pigments_tfjt_fk` FOREIGN KEY (`trees_pk`,`flights_pk`) REFERENCES `trees_flights_join_tbl` (`trees_pk`,`flights_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pigments`
--

LOCK TABLES `pigments` WRITE;
/*!40000 ALTER TABLE `pigments` DISABLE KEYS */;
/*!40000 ALTER TABLE `pigments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `unispec`
--

DROP TABLE IF EXISTS `unispec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unispec` (
  `trees_pk` int NOT NULL,
  `flights_pk` int NOT NULL,
  `pigment` int NOT NULL,
  `value` decimal(20,15) NOT NULL,
  PRIMARY KEY (`trees_pk`,`flights_pk`,`pigment`),
  CONSTRAINT `unispec_tfjt_fk` FOREIGN KEY (`trees_pk`,`flights_pk`) REFERENCES `trees_flights_join_tbl` (`trees_pk`,`flights_pk`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `unispec`
--

LOCK TABLES `unispec` WRITE;
/*!40000 ALTER TABLE `unispec` DISABLE KEYS */;
/*!40000 ALTER TABLE `unispec` ENABLE KEYS */;
UNLOCK TABLES;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-16 00:00:00
