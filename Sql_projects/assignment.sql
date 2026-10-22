WEEK 2 ASSIGNMENT
---SECTION A------
--creating a schema called greenwood_academy--
create schema greenwood_academy;
--set path to schema--
set search_path to greenwood_academy;
--create table called Students with the following colimns--
create table Students(
	student_id	INT	PRIMARY key,
	first_name	VARCHAR(50)	NOT null,
	last_name	VARCHAR(50)	NOT null,
	gender	VARCHAR(1),
	date_of_birth	DATE,
	class	VARCHAR(10),
	city	VARCHAR(50)
);
-- create table called subjects with the following colums
create table Subjects(
	subject_id	INT	PRIMARY key UNIQUE,
	subject_name	VARCHAR(100) NOT NULL,
	department	VARCHAR(50),
	teacher_name	VARCHAR(100),
	credits	INT
);
-- create table called exam_results with the following colums
create table exam_results(
	result_id	INT	PRIMARY key,
	student_id	INT	NOT null,
	subject_id	INT	NOT null,
	marks	INT	NOT null,
	exam_date	DATE,
	grade	VARCHAR(2)
);
--SECTION B--
insert into Students(student_id,first_name,last_name,gender,date_of_birth,class,city)
Values
(1, 'Amina','Wanjiku','F','2008-03-12','Form 3','Nairobi'),
(2, 'Brian','Ochieng','M','2007-07-25','Form 4','Mombasa'),
(3, 'Cynthia','Mutua','F','2008-11-05',	'Form 3','Kisumu'),
(4,	'David','Kamau','M','2007-02-18','Form 4','Nairobi'),
(5,	'Esther','Akinyi','F','2009-06-30','Form 2','Nakuru'),
(6,	'Felix','Otieno','M','2009-09-14','Form 2','Eldoret'),
(7,	'Grace','Mwangi','F','2008-01-22','Form 3','Nairobi'),
(8,	'Hassan','Abdi','M','2007-04-09','Form 4','Mombasa'),
(9,	'Ivy','Chebet','F','2009-12-01','Form 2','Nakuru'),
(10,'James','Kariuki','M','2008-08-17','Form 3','Nairobi');
insert into Subjects (subject_id,subject_name,department,teacher_name,credits)
values
(1,'Mathematics','Sciences','Mr. Njoroge',4),
(2,'English','Languages','Ms. Adhiambo',3),
(3,'Biology','Sciences','Ms. Otieno',4),
(4,'History','Humanities','Mr. Waweru',3),
(5,'Kiswahili','Languages','Ms. Nduta',3),
(6,'Physics','Sciences','Mr. Kamande',4),
(7,'Geography','Humanities','Ms. Chebet',3),
(8,'Chemistry','Sciences','Ms. Muthoni',4),
(9,'Computer Studies','Sciences','Mr. Oduya',3),
(10,'Business Studies',	'Humanities','Ms. Wangari',3);
insert into exam_results(result_id,student_id,subject_id,marks,exam_date,grade)
values
(1,	1,  1,	78,	'2024-03-15',	'B'),
(2,	1,	2,	85,	'2024-03-16',	'A'),
(3,	2,	1,	92,	'2024-03-15',	'A'),
(4,	2,	3,	55,	'2024-03-17',	'C'),
(5,	3,	2,	49,	'2024-03-16',	'D'),
(6,	3,	4,	71,	'2024-03-18',	'B'),
(7,	4,	1,	88,	'2024-03-15',	'A'),
(8,	4,	6,	63,	'2024-03-19',   'C'),
(9,	5,	5,	39,	'2024-03-20',   'F'),
(10, 6,	9,	95,	'2024-03-21',	'A');
select * from exam_results;
select * from  Subjects;
select * from  Students;
-- adding a column on students--
/*syntax--
alter table table_name
add column_name datatype;*/
alter table Students
add phone_number VARCHAR(20);
--renaming credits to credit_hours--
/*   syntax
alter table  table_name
rename column old_name to new_name;*/
alter  table subjects
rename column credits to credit_hours;
--remove the phone_number column--
/*  syntax
alter table table_name
drop column_name;*/
alter table Students
drop phone_number;
--SECTION C--
/*
update table_name
set column_name = value1,value2,value3
where condition
*/
--Updating esther akinyi city infor--
update Students
set city = 'Nairobi'
where student_id = 5;
-- update marks for id=5 --
update exam_results
set marks = 59
where result_id = 5;
--update grade for result_id--
update exam_results
set grade = 'C'
where result_id = 5;
--remove exam result_id=9--
delete  from exam_results
where result_id = 9;
--all stuudent in form 4-
--Total_form_4_students = 3 --
select Count(class) as Total_form_4_students
from students
where class ='Form 4';
--subjects in science department--
--total_subjects_in_science_department=5
select  Count(subjects) as total_subjects_in_science_department
from  Subjects
where department= 'Sciences';
---all exam result where results are greater than 70%--
--number_of_or_greater_than_70 = 6--
select count(marks) as number_of_or_greater_than_70
from exam_results
where marks >=70;
--number of students who are feamles--
--number_of_female_students =5
select count(gender) as number_of_female_students
from students
where gender='F';
--form 3 students from Nairobi--
select *
from students
where class ='Form 3'
and city='Nairobi';
--student in form 2 or form 4 ---
select *
from students
where class ='Form 4'
or class ='Form 2';
--SECTION D---
/*
SELECT column1, column2, ...
FROM table_name
WHERE column_name BETWEEN value1 AND value2;
*/
--marks between 50 and 80
select  marks
from exam_results
where marks between  50 and 80;
--exams that took place between 15th March 2024 and 18th March 2024.
select *
from exam_results
where exam_date between '2023-03-15' and '2024-03-18';
-- students who live in Nairobi, Mombasa, or Kisumu--
select first_name,last_name,city
from
students
where city in ('Nairobi','Mombasa','Kisumu');
--students who are NOT in Form 2 or Form 3--
select first_name,last_name
from students
where class
not in ('Form 2','Form 3');
--students whose first name starts with the letter 'A' or 'E'
select first_name
from
students
where  first_name like 'A%' or first_name like 'E%';
--subjects whose subject name contains the word 'Studies'
select subject_name
from
subjects
where  subject_name like '%Studies%';
--SECTION E--
/*
SELECT COUNT( column_name )
FROM table_name
WHERE condition;
*/
--How many students are currently in Form 3
select count(student_id)as number_of_students_in_form3
from students
where class = 'Form 3';
---How many exam results have a mark of 70 or above
select count(marks) as number_of_or_greater_than_70
from exam_results
where marks >=70;
--SECTION  F--
/*
CASE expression
   WHEN value1 THEN result1
      WHEN value2 THEN result2
         ELSE default_result
END
*/
--label each exam result with a grade description--
select subject_id,grade,marks,
      case
	      	when marks >=80 then 'Distinction'
			      	when marks >=60 then 'Merit'
					      	when marks >=40  then 'Pass'
							      	else 'Fail'
									      end  as grade_description   
									from exam_results;
									--categorise into senior or junior--
									select first_name,last_name,class,
									     case
										     	when class = 'Form 3' or class = 'Form 4' then 'Senior'
												     	when class ='Form 2' or class = 'Form 1' then 'Junior'
														     else null
															     end as student_level
															from students; 
															q
