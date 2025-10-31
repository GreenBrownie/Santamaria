CREATE DATABASE IF NOT EXISTS partidosBD;

USE partidosBD;

CREATE TABLE PartidosML (
    id_partido INT PRIMARY KEY AUTO_INCREMENT,

    fecha DATE,
    hora TIME,
    
    equipo_local VARCHAR(50),
    equipo_visitante VARCHAR(50),
    id_equipo_local INT,
    id_equipo_visitante INT, -- Tienen que coinicidir con EquiposRef ¿Realmente mejorará el performance? No estoy sobresimplificando?
    
    goles_local_final INT,
    goles_visitante_final INT,
    resultado_final VARCHAR(1), -- H/D/A futura predicción en % 
    goles_local_ht INT,
    goles_visitante_ht INT, 
    resultado_ht VARCHAR(1),
    disparos_local INT,
    disparos_visitante INT,
    disparos_porteria_local INT,
    disparos_porteria_visitante INT,
    corners_local INT,partidosbd
    corners_visitante INT,
    faltas_local INT,
    faltas_visitante INT,
    amarillas_local INT,
    amarillas_visitante INT,
    rojas_local INT,
    rojas_visitante INT
    
);

CREATE TABLE EquiposRef (
    id_equipo INT PRIMARY KEY AUTO_INCREMENT,
    nombre_equipo VARCHAR(50) UNIQUE
);
