/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: data_info
-- ------------------------------------------------------
-- Server version	11.8.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `job_info`
--

DROP TABLE IF EXISTS `job_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `job_info` (
  `job_id` int(11) NOT NULL AUTO_INCREMENT,
  `job_title` varchar(50) DEFAULT NULL,
  `avg_salary` int(11) DEFAULT NULL,
  PRIMARY KEY (`job_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `job_info`
--

LOCK TABLES `job_info` WRITE;
/*!40000 ALTER TABLE `job_info` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `job_info` VALUES
(1,'백엔드 개발자',6500),
(2,'프론트엔드 개발자',6000),
(3,'데이터 엔지니어',7000),
(4,'AI 연구원',7500),
(5,'보안 엔지니어',7200),
(6,'시스템 관리자',5800),
(7,'QA 엔지니어',5000),
(8,'프로젝트 매니저',6800),
(9,'UI/UX 디자이너',5500),
(10,'DB 관리자',6600);
/*!40000 ALTER TABLE `job_info` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `tool_info`
--

DROP TABLE IF EXISTS `tool_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tool_info` (
  `tool_id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Tool 고유 ID',
  `tool_name` varchar(100) NOT NULL COMMENT 'Tool 호출 이름 (예: select_user_list)',
  `tool_desc` varchar(255) DEFAULT NULL COMMENT 'Tool 설명',
  `tool_type` varchar(50) NOT NULL COMMENT 'Tool 유형 (DB, DB_MAPPER, API, FILE 등)',
  `exec_target` varchar(500) DEFAULT NULL COMMENT '실행 대상 (SQL문 / Mapper.method / API URL)',
  `http_method` varchar(10) DEFAULT NULL COMMENT 'API 호출 시 HTTP 메서드 (GET, POST 등)',
  `enabled` char(1) DEFAULT 'Y' COMMENT '사용 여부 (Y/N)',
  `created_at` datetime DEFAULT current_timestamp() COMMENT '생성 일시',
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '수정 일시',
  PRIMARY KEY (`tool_id`),
  UNIQUE KEY `tool_name` (`tool_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='MCP Tool 메타데이터 (혼합 구조 대응형)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tool_info`
--

LOCK TABLES `tool_info` WRITE;
/*!40000 ALTER TABLE `tool_info` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `tool_info` VALUES
(1,'get_user_info','유저 정보 조회','DB_MAPPER','getUserInfo',NULL,'Y','2025-11-04 16:59:52','2025-11-04 16:59:52');
/*!40000 ALTER TABLE `tool_info` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `user_info`
--

DROP TABLE IF EXISTS `user_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_info` (
  `ssn` char(14) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `gender` char(1) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `job_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`ssn`),
  KEY `job_id` (`job_id`),
  CONSTRAINT `user_info_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `job_info` (`job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_info`
--

LOCK TABLES `user_info` WRITE;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `user_info` VALUES
('900101-1000001','김철수',35,'M','kimcs1@example.com',1),
('900102-1000002','이영희',32,'F','leeyh2@example.com',1),
('900103-1000003','박민수',40,'M','parkms3@example.com',1),
('900104-1000004','최지현',28,'F','choijh4@example.com',1),
('900105-1000005','정우성',31,'M','jungws5@example.com',1),
('900106-1000006','한가인',34,'F','hanga6@example.com',1),
('900107-1000007','오세훈',29,'M','ohsh7@example.com',1),
('900108-1000008','유재석',41,'M','yjs8@example.com',1),
('900109-1000009','강호동',44,'M','kanghd9@example.com',1),
('900110-1000010','장원영',23,'F','jangwy10@example.com',1),
('900111-1000011','안유진',22,'F','anyu11@example.com',2),
('900112-1000012','이서준',27,'M','leesj12@example.com',2),
('900113-1000013','정세운',25,'M','jungsw13@example.com',2),
('900114-1000014','하정우',42,'M','hahjw14@example.com',2),
('900115-1000015','배수지',29,'F','baesu15@example.com',2),
('900116-1000016','공유',38,'M','gongy16@example.com',2),
('900117-1000017','송혜교',40,'F','songhg17@example.com',2),
('900118-1000018','조인성',41,'M','join18@example.com',2),
('900119-1000019','김태리',31,'F','kimtr19@example.com',2),
('900120-1000020','류준열',34,'M','ryujy20@example.com',2),
('900121-1000021','손예진',39,'F','sonyj21@example.com',3),
('900122-1000022','박보검',31,'M','parkbg22@example.com',3),
('900123-1000023','이도현',28,'M','leodh23@example.com',3),
('900124-1000024','한소희',29,'F','hansh24@example.com',3),
('900125-1000025','김우빈',33,'M','kimwb25@example.com',3),
('900126-1000026','김지원',32,'F','kimjw26@example.com',3),
('900127-1000027','이광수',38,'M','leegs27@example.com',3),
('900128-1000028','전지현',42,'F','junhj28@example.com',3),
('900129-1000029','박신혜',33,'F','parksh29@example.com',3),
('900130-1000030','서강준',31,'M','seogj30@example.com',3),
('900131-1000031','문채원',35,'F','mooncw31@example.com',4),
('900132-1000032','유아인',38,'M','yooi32@example.com',4),
('900133-1000033','김하늘',39,'F','kimhn33@example.com',4),
('900134-1000034','이하늬',37,'F','leehn34@example.com',4),
('900135-1000035','김남길',43,'M','kimng35@example.com',4),
('900136-1000036','정은지',32,'F','jungej36@example.com',4),
('900137-1000037','차은우',27,'M','chaew37@example.com',4),
('900138-1000038','박서준',35,'M','parkse38@example.com',4),
('900139-1000039','이하린',25,'F','leehr39@example.com',4),
('900140-1000040','홍진호',39,'M','hongjh40@example.com',4),
('900141-1000041','전소민',37,'F','jeonsm41@example.com',5),
('900142-1000042','김종국',47,'M','kimjk42@example.com',5),
('900143-1000043','하하',44,'M','haha43@example.com',5),
('900144-1000044','이효리',44,'F','leehy44@example.com',5),
('900145-1000045','김민정',36,'F','kimmj45@example.com',5),
('900146-1000046','유인나',39,'F','yoinn46@example.com',5),
('900147-1000047','서지석',40,'M','seoj47@example.com',5),
('900148-1000048','한지민',42,'F','hanjm48@example.com',5),
('900149-1000049','윤계상',43,'M','yunky49@example.com',5),
('900150-1000050','이준기',41,'M','leejg50@example.com',5),
('900151-1000051','문근영',36,'F','moongy51@example.com',6),
('900152-1000052','김새론',24,'F','kimsa52@example.com',6),
('900153-1000053','박보영',33,'F','parkby53@example.com',6),
('900154-1000054','이성민',53,'M','leesm54@example.com',6),
('900155-1000055','정유미',38,'F','jungym55@example.com',6),
('900156-1000056','정해인',35,'M','junghi56@example.com',6),
('900157-1000057','공효진',43,'F','gonghj57@example.com',6),
('900158-1000058','조정석',44,'M','jojsk58@example.com',6),
('900159-1000059','이선균',48,'M','leesg59@example.com',6),
('900160-1000060','손석구',40,'M','sons60@example.com',6),
('900161-1000061','이하준',33,'M','leehj61@example.com',7),
('900162-1000062','김유정',26,'F','kimyj62@example.com',7),
('900163-1000063','신민아',39,'F','shinma63@example.com',7),
('900164-1000064','이동욱',42,'M','leedw64@example.com',7),
('900165-1000065','박해진',39,'M','parkhj65@example.com',7),
('900166-1000066','정려원',43,'F','junglw66@example.com',7),
('900167-1000067','조보아',33,'F','joboa67@example.com',7),
('900168-1000068','이정은',47,'F','leeej68@example.com',7),
('900169-1000069','류승룡',53,'M','ryusr69@example.com',7),
('900170-1000070','마동석',53,'M','madong70@example.com',7),
('900171-1000071','이성경',33,'F','leesg71@example.com',8),
('900172-1000072','이광복',50,'M','leegb72@example.com',8),
('900173-1000073','정경호',41,'M','jungkh73@example.com',8),
('900174-1000074','신세경',34,'F','shinsk74@example.com',8),
('900175-1000075','최수영',34,'F','choisy75@example.com',8),
('900176-1000076','이유리',42,'F','leeyr76@example.com',8),
('900177-1000077','강민혁',33,'M','kangmh77@example.com',8),
('900178-1000078','이재윤',38,'M','leejy78@example.com',8),
('900179-1000079','손호준',40,'M','sonhj79@example.com',8),
('900180-1000080','홍은희',44,'F','honguh80@example.com',8),
('900181-1000081','김유리',32,'F','kimyr81@example.com',9),
('900182-1000082','정소민',35,'F','jungs82@example.com',9),
('900183-1000083','이유비',32,'F','leeyb83@example.com',9),
('900184-1000084','이준영',28,'M','leejy84@example.com',9),
('900185-1000085','서예지',33,'F','seoyj85@example.com',9),
('900186-1000086','김소현',25,'F','kimsh86@example.com',9),
('900187-1000087','박형식',33,'M','parkhs87@example.com',9),
('900188-1000088','이상윤',42,'M','leesy88@example.com',9),
('900189-1000089','김동욱',40,'M','kimdw89@example.com',9),
('900190-1000090','정은채',36,'F','jungec90@example.com',9),
('900191-1000091','최민식',58,'M','choims91@example.com',10),
('900192-1000092','송강호',57,'M','songkh92@example.com',10),
('900193-1000093','이병헌',55,'M','leebh93@example.com',10),
('900194-1000094','전도연',52,'F','jeondy94@example.com',10),
('900195-1000095','김혜수',51,'F','kimhs95@example.com',10),
('900196-1000096','황정민',53,'M','hwangjm96@example.com',10),
('900197-1000097','임수정',42,'F','imsj97@example.com',10),
('900198-1000098','박해일',46,'M','parkhi98@example.com',10),
('900199-1000099','조승우',44,'M','josw99@example.com',10),
('900200-1000100','수지',29,'F','suzy100@example.com',10);
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `weather_info`
--

DROP TABLE IF EXISTS `weather_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `weather_info` (
  `date` char(8) NOT NULL,
  `weather` varchar(10) DEFAULT NULL,
  `temperature` decimal(4,1) DEFAULT NULL,
  `humidity` int(11) DEFAULT NULL,
  PRIMARY KEY (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `weather_info`
--

LOCK TABLES `weather_info` WRITE;
/*!40000 ALTER TABLE `weather_info` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `weather_info` VALUES
('20250723','맑음',28.3,55),
('20250724','흐림',26.8,60),
('20250725','비',24.5,80),
('20250726','맑음',27.7,58),
('20250727','구름많음',25.1,63),
('20250728','맑음',29.2,48),
('20250729','비',23.8,82),
('20250730','맑음',30.1,50),
('20250731','흐림',27.6,65),
('20250801','맑음',31.0,46),
('20250802','비',24.3,84),
('20250803','맑음',28.9,53),
('20250804','흐림',26.7,60),
('20250805','맑음',30.4,48),
('20250806','비',22.9,88),
('20250807','맑음',29.8,55),
('20250808','구름많음',27.2,61),
('20250809','맑음',30.6,49),
('20250810','비',23.4,83),
('20250811','흐림',26.3,64),
('20250812','맑음',28.8,52),
('20250813','비',24.1,79),
('20250814','맑음',31.2,45),
('20250815','맑음',32.0,44),
('20250816','흐림',27.8,62),
('20250817','맑음',29.9,50),
('20250818','비',23.5,85),
('20250819','맑음',28.1,56),
('20250820','구름많음',26.5,59),
('20250821','맑음',30.0,51),
('20250822','비',24.9,81),
('20250823','맑음',31.3,47),
('20250824','흐림',27.1,63),
('20250825','맑음',29.5,54),
('20250826','비',23.7,83),
('20250827','맑음',30.8,49),
('20250828','구름많음',28.0,57),
('20250829','맑음',31.1,46),
('20250830','비',25.2,79),
('20250831','흐림',26.9,62),
('20250901','맑음',28.6,55),
('20250902','비',24.0,85),
('20250903','맑음',30.2,50),
('20250904','맑음',29.4,53),
('20250905','흐림',27.7,61),
('20250906','맑음',31.0,48),
('20250907','비',23.9,84),
('20250908','맑음',28.5,56),
('20250909','구름많음',26.8,60),
('20250910','맑음',30.7,49),
('20250911','비',24.6,82),
('20250912','맑음',31.5,47),
('20250913','흐림',27.3,64),
('20250914','맑음',29.6,52),
('20250915','비',23.8,87),
('20250916','맑음',30.9,50),
('20250917','구름많음',28.2,58),
('20250918','맑음',31.4,45),
('20250919','비',24.4,86),
('20250920','맑음',29.1,54),
('20250921','흐림',26.6,63),
('20250922','맑음',30.5,49),
('20250923','비',23.6,83),
('20250924','맑음',31.6,46),
('20250925','구름많음',27.9,60),
('20250926','맑음',29.8,52),
('20250927','비',25.0,78),
('20250928','흐림',27.0,64),
('20250929','맑음',30.3,48),
('20250930','맑음',29.0,55),
('20251001','비',24.2,85),
('20251002','맑음',31.2,46),
('20251003','흐림',27.4,61),
('20251004','맑음',30.0,50),
('20251005','비',23.9,83),
('20251006','맑음',29.4,53),
('20251007','구름많음',27.7,59),
('20251008','맑음',31.0,47),
('20251009','비',25.1,80),
('20251010','맑음',30.8,49),
('20251011','흐림',27.6,62),
('20251012','맑음',29.9,52),
('20251013','비',23.7,84),
('20251014','맑음',31.4,45),
('20251015','구름많음',28.1,58),
('20251016','맑음',30.5,50),
('20251017','비',24.3,83),
('20251018','맑음',31.1,47),
('20251019','흐림',27.5,63),
('20251020','맑음',29.7,53),
('20251021','비',25.0,79),
('20251022','맑음',30.9,49),
('20251023','구름많음',28.3,57),
('20251024','맑음',31.3,46),
('20251025','비',24.8,81),
('20251026','흐림',27.2,61),
('20251027','맑음',29.6,52),
('20251028','비',23.5,85),
('20251029','맑음',30.7,48),
('20251030','맑음',29.3,55);
/*!40000 ALTER TABLE `weather_info` ENABLE KEYS */;
UNLOCK TABLES;
commit;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-11-05  9:41:49
