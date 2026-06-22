-- MySQL dump 10.13  Distrib 9.4.0, for Linux (x86_64)
--
-- Host: localhost    Database: gaia
-- ------------------------------------------------------
-- Server version	9.4.0
--
-- Curated TEST FIXTURE for the `gaia` bind (BAR_API local/CI) — NOT a prod dump
-- (read-only access blocks mysqldump). Small by design; each row group trips one
-- rule of GET /gaia/publication_figures_by_gene/<identifier>:
--   * PMC151246 (real PMID 12045268, figs 01-0441f1..f5): abi3 OCR'd on f2+f4 only.
--   * abi3/abi5 (gene:false) on variantfig.jpg : word-boundary match must CATCH.
--   * gabi390_r (gene:false) on gabitest.jpg    : word-boundary match must REJECT.
--   * gr1.jpg in two publications               : bare-name guard must DROP.
--   * nullfig.jpg (NULL img_url)                : null-url skip must DROP.
--   * gene 2 (alias NOMATCH4)                   : empty-payload (200, not 404) path.
-- figure_models.imageName keeps a leading "/" to exercise TRIM(LEADING '/' ...).
-- DDL matched to prod SHOW CREATE TABLE (2026-06-20). FK constraints intentionally
-- omitted (they do not affect read queries; keeps the fixture load-order-independent).

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
-- Current Database: `gaia`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `gaia` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `gaia`;

--
-- Table structure for table `genes`
--

DROP TABLE IF EXISTS `genes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `genes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `species` varchar(64) NOT NULL,
  `locus` varchar(64) DEFAULT NULL,
  `geneid` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_locus` (`locus`),
  KEY `idx_geneid` (`geneid`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `genes`
--

LOCK TABLES `genes` WRITE;
/*!40000 ALTER TABLE `genes` DISABLE KEYS */;
INSERT INTO `genes` VALUES (1,'Arabidopsis_thaliana','At3g24650','822061'),(2,'Arabidopsis_thaliana','At1g01010','000001');
/*!40000 ALTER TABLE `genes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `aliases`
--

DROP TABLE IF EXISTS `aliases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aliases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `genes_id` int NOT NULL,
  `alias` varchar(256) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_genes` (`genes_id`),
  KEY `idx_aliases` (`alias`,`genes_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `aliases`
--

LOCK TABLES `aliases` WRITE;
/*!40000 ALTER TABLE `aliases` DISABLE KEYS */;
INSERT INTO `aliases` VALUES (1,1,'ABI3'),(2,1,'SIS10'),(3,1,'AtABI3'),(4,1,'ABA INSENSITIVE 3'),(5,1,'ABSCISIC ACID INSENSITIVE 3'),(6,1,'SUGAR INSENSITIVE 10'),(7,2,'NOMATCH4');
/*!40000 ALTER TABLE `aliases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `publication_figures`
--

DROP TABLE IF EXISTS `publication_figures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `publication_figures` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(512) DEFAULT NULL,
  `abstract` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `publication_figures`
--
-- NOTE: pub 60 (PMC6403161) title/abstract are stored TRUNCATED in the prod corpus
-- (title ends "... Responses in ", abstract ends "... selected family members in ") — kept VERBATIM.

LOCK TABLES `publication_figures` WRITE;
/*!40000 ALTER TABLE `publication_figures` DISABLE KEYS */;
INSERT INTO `publication_figures` VALUES (10,'Abscisic acid signaling in seeds and seedlings.','Review of ABA signaling pathways in seeds and seedlings.'),(20,'Unrelated paper A (collision partner 1).','Abstract A.'),(30,'Unrelated paper B (collision partner 2 + null url).','Abstract B.'),(40,'Unrelated paper C (false-positive container).','Abstract C.'),(60,'AP2/ERF Transcription Factor Regulatory Networks in Hormone and Abiotic Stress Responses in ','Dynamic environmental changes such as extreme temperature, water scarcity and high salinity affect plant growth, survival, and reproduction. Plants have evolved sophisticated regulatory mechanisms to adapt to these unfavorable conditions, many of which interface with plant hormone signaling pathways. Abiotic stresses alter the production and distribution of phytohormones that in turn mediate stress responses at least in part through hormone- and stress-responsive transcription factors. Among these, the APETALA2/ETHYLENE RESPONSIVE FACTOR (AP2/ERF) family transcription factors (AP2/ERFs) have emerged as key regulators of various stress responses, in which they also respond to hormones with improved plant survival during stress conditions. Apart from participation in specific stresses, AP2/ERFs are involved in a wide range of stress tolerance, enabling them to form an interconnected stress regulatory network. Additionally, many AP2/ERFs respond to the plant hormones abscisic acid (ABA) and ethylene (ET) to help activate ABA and ET dependent and independent stress-responsive genes. While some AP2/ERFs are implicated in growth and developmental processes mediated by gibberellins (GAs), cytokinins (CTK), and brassinosteroids (BRs). The involvement of AP2/ERFs in hormone signaling adds the complexity of stress regulatory network. In this review, we summarize recent studies on AP2/ERF transcription factors in hormonal and abiotic stress responses with an emphasis on selected family members in ');
/*!40000 ALTER TABLE `publication_figures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `figures`
--

DROP TABLE IF EXISTS `figures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `figures` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publication_figures_id` int NOT NULL,
  `img_name` varchar(64) NOT NULL,
  `caption` text,
  `img_url` varchar(265) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_publication_figures_figures` (`publication_figures_id`)
) ENGINE=InnoDB AUTO_INCREMENT=601 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `figures`
--

LOCK TABLES `figures` WRITE;
/*!40000 ALTER TABLE `figures` DISABLE KEYS */;
INSERT INTO `figures` VALUES (100,10,'01-0441f1.jpg','Domain Structure of B3 and bZIP Domain Transcription Factors','https://cdn.ncbi.nlm.nih.gov/pmc/blobs/82d7/151246/8e4f6ebe4139/01-0441f1.jpg'),(101,10,'01-0441f2.jpg','Scheme of Signaling Pathways in Seed Development.','https://cdn.ncbi.nlm.nih.gov/pmc/blobs/82d7/151246/a56d4d6d5560/01-0441f2.jpg'),(102,10,'01-0441f3.jpg','Regulation of ABA-Responsive Promoter Activity in a Rice Embryo Protoplast','https://cdn.ncbi.nlm.nih.gov/pmc/blobs/82d7/151246/67ad8027f184/01-0441f3.jpg'),(103,10,'01-0441f4.jpg','Scheme of Signaling Pathways That Interact with the ABA Regulation of Germination.','https://cdn.ncbi.nlm.nih.gov/pmc/blobs/82d7/151246/7be9f20adc7b/01-0441f4.jpg'),(104,10,'01-0441f5.jpg','Sensitivity of Seedlings of Wild-Type, abi, and ABI Overexpressing Lines','https://cdn.ncbi.nlm.nih.gov/pmc/blobs/82d7/151246/3c7ab6e933bb/01-0441f5.jpg'),(200,20,'gr1.jpg','Collision figure (pub A).','https://example.org/PMC900001/gr1.jpg'),(300,30,'gr1.jpg','Collision figure (pub B).','https://example.org/PMC900002/gr1.jpg'),(301,30,'nullfig.jpg','Figure with no URL.',NULL),(400,40,'gabitest.jpg','GABI line figure (false-positive bait).','https://example.org/PMC900003/gabitest.jpg'),(600,60,'fpls-10-00228-g003.jpg','AP2/ERFs roles in hormone pathways. Abiotic stresses alter the production and distribution of phytohormones that in turn mediate stresses responses through hormone signaling components and AP2/ERFs. Arrows and bar ends indicate activation and repression effect, respectively. Figure is created with BioRender.','https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9ceb/6403161/d18acaa7332e/fpls-10-00228-g003.jpg');
/*!40000 ALTER TABLE `figures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pub_ids`
--

DROP TABLE IF EXISTS `pub_ids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pub_ids` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publication_figures_id` int NOT NULL,
  `pubmed` varchar(16) DEFAULT NULL,
  `pmc` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_publication_figures_pub_ids` (`publication_figures_id`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pub_ids`
--

LOCK TABLES `pub_ids` WRITE;
/*!40000 ALTER TABLE `pub_ids` DISABLE KEYS */;
INSERT INTO `pub_ids` VALUES (10,10,'12045268','PMC151246'),(20,20,'30000001','PMC900001'),(30,30,'30000002','PMC900002'),(40,40,'30000003','PMC900003'),(60,60,'30873200','PMC6403161');
/*!40000 ALTER TABLE `pub_ids` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `author_list`
--

DROP TABLE IF EXISTS `author_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `author_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publication_figures_id` int NOT NULL,
  `author` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_publication_figures_author_list` (`publication_figures_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `author_list`
--

LOCK TABLES `author_list` WRITE;
/*!40000 ALTER TABLE `author_list` DISABLE KEYS */;
INSERT INTO `author_list` VALUES (1,10,'Finkelstein RR'),(2,10,'Gampala SSL'),(3,10,'Rock CD'),(5,60,'Zhouli Xie'),(6,60,'Trevor M Nolan'),(7,60,'Hao Jiang'),(8,60,'Yanhai Yin');
/*!40000 ALTER TABLE `author_list` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `figure_models`
--

DROP TABLE IF EXISTS `figure_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `figure_models` (
  `id` int NOT NULL AUTO_INCREMENT,
  `data` json DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `figure_models`
--

LOCK TABLES `figure_models` WRITE;
/*!40000 ALTER TABLE `figure_models` DISABLE KEYS */;
INSERT INTO `figure_models` VALUES (1,'{"gene": true, "word": "abi3", "image": [{"bbox": [[[268,108],[317,108],[317,118],[268,118]],[[45,110],[72,111],[72,120],[45,119]]], "imageName": "/01-0441f2.jpg"},{"bbox": [[[274,96],[298,96],[298,105],[274,105]]], "imageName": "/01-0441f4.jpg"},{"bbox": [[[10,10],[40,10],[40,20],[10,20]]], "imageName": "/gr1.jpg"},{"bbox": [[[5,5],[25,5],[25,15],[5,15]]], "imageName": "/nullfig.jpg"}]}'),(3,'{"gene": false, "word": "gabi390_r", "image": [{"bbox": [[[200,200],[260,200],[260,212],[200,212]]], "imageName": "/gabitest.jpg"}]}'),(4,'{"gene": false, "word": "abi3/vp1", "image": [{"bbox": [[[34, 357], [96, 357], [96, 369], [34, 369]]], "imageName": "/fpls-10-00228-g003.jpg"}]}');
/*!40000 ALTER TABLE `figure_models` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed