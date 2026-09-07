CREATE DATABASE IF NOT EXISTS school_db;

USE school_db;

CREATE TABLE bridge (
    ID INT,
    FullName TEXT,
    Sex TEXT,
    Class TEXT
);

CREATE TABLE chess (
    ID INT,
    FullName TEXT,
    Sex TEXT,
    Class TEXT
);

CREATE TABLE music (
    ID INT,
    Type TEXT
);

CREATE TABLE student (
    ID INT,
    FullName VARCHAR(100),
    DOB VARCHAR(20),
    Sex VARCHAR(10),
    Class VARCHAR(10),
    HCode VARCHAR(10),
    DCode VARCHAR(10),
    Remission BINARY(1),
    MTest INT,
    PTest INT
);
