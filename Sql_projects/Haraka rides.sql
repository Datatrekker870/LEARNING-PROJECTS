create schema haraka_hailing_cab;
set search_path to haraka_hailing_cab;



create table trips_staging(
trip_id text primary key,
customer_name text,
customer_phone text,
customer_area text,
driver_name text,
driver_phone text,
vehicle_plate text,
vehicle_make text,
vehicle_model text,
pickup_area text,
drpoff_area text,
trip_date text,
pickup_time text,
distance_km text,
payment_method text,
status text,
fare_amount text,
customer_rating text
);

create table fleet_staging (
log_id text,
vehicle_plate text,
vehicle_make text,
vehicle_model text,
vehicle_year text,
vehicle_type text,
vehicle_status text,
event_type text,
event_date text,
litres text,
fuel_cost  text,
odometer_reading text,
station_name text,
service_type text,
maintenance_cost text,
mechanic_name text,
next_service_due text
);
---=================================================---------
---================================================----------
----CLEANING fleet_staging table---
select * from fleet_staging t; 
select * from trips_staging ts; 

--drop empty column litres--
alter table fleet_staging
drop column litres;

--remove empty column drp_off--
alter table trips_staging 
drop column drpoff_area;

--Phase 2 - Profile the Mess--
select COUNT(*) from fleet_staging t; ---106rows
select COUNT(*) from trips_staging ts ; --400rows

--fleet_staging interrogations--
select t.log_id  from fleet_staging t
where t.log_id  is null ; --- log_id column has no null values--

ALTER TABLE fleet_staging 
ALTER COLUMN log_id TYPE text USING log_id::integer;

select t.vehicle_plate  from fleet_staging t
where t.vehicle_plate is null ; ---vehicle_plate has no null values--

select TRIM(UPPER(t.vehicle_plate))  from fleet_staging t;
update  fleet_staging
set vehicle_plate = TRIM(UPPER(vehicle_plate)); --update the clean column--


select t.vehicle_make  from fleet_staging t
where t.vehicle_make is null ;  ---vehicle_make has no  null values--

select TRIM(UPPER(t.vehicle_make))  from fleet_staging t;
update  fleet_staging
set vehicle_make = TRIM(UPPER(vehicle_make)); --update the clean column--

select t.vehicle_model  from fleet_staging t
where t.vehicle_model is null;---vehicle_model has no  null values--

select TRIM(UPPER(t.vehicle_model))  from fleet_staging t;
update  fleet_staging
set vehicle_model = TRIM(UPPER(vehicle_model)); --update the clean column--

select vehicle_type from fleet_staging t
where  vehicle_type is null; -- vehicle_type  no  null values--

select TRIM(UPPER(t.vehicle_type ))  from fleet_staging t;
update  fleet_staging
set vehicle_type = TRIM(UPPER(vehicle_type)); --update the clean column--

                                                                                                                                                                                                                                                           

alter table fleet_staging
add column vehicle_type text;

alter table fleet_staging
drop  column vehicle_type;
select t.vehicle_status  from fleet_staging t
where  t.vehicle_status is null; -- vehicle_status  no  null values--

select TRIM(UPPER(t.vehicle_status  )) from fleet_staging t;
update  fleet_staging
set vehicle_status= TRIM(UPPER(vehicle_status)); --update the clean column--

select t.event_type   from fleet_staging t
where  t.event_type  is null;  -- event_type  no  null values--

select TRIM(UPPER(t.event_type)) from fleet_staging t;
update  fleet_staging
set event_type= TRIM(UPPER(event_type));

select t.event_date    from fleet_staging t
where  t.event_date   is null;  -- event_date  no  null values--


select FORMAT((t.event_date ),'dd-MM-yyyy') from fleet_staging t;
update  fleet_staging
set event_date= FORMAT((event_date),'dd-MM-yyyy');


select t.fuel_cost   from fleet_staging t
where  t.fuel_cost   is null;  -- fuel_cost  no  null values--


select TRIM(REPLACE(t.fuel_cost,'KES','' )) from fleet_staging  t;
update  fleet_staging
set fuel_cost = TRIM(REPLACE(fuel_cost,'KES',''));


select t.odometer_reading    from fleet_staging t
where  t.odometer_reading    is null;  -- odometer_reader  no  null values--


select t.station_name    from fleet_staging t
where  t.station_name    is null;  -- station_name  no  null values--


select TRIM(UPPER(t.station_name)) from fleet_staging t;
update  fleet_staging
set station_name = TRIM(UPPER(station_name));


select t.service_type     from fleet_staging t
where  t.service_type     is null;  -- service_type  no  null values--


select TRIM(UPPER(t.service_type )) from fleet_staging t;
update  fleet_staging
set service_type = TRIM(UPPER(service_type ));


select t.mechanic_name    from fleet_staging t
where  t.maintenance_cost  is null;  -- maintenance_cost  no  null values--

select TRIM(REPLACE(t.maintenance_cost,'KES','' )) from fleet_staging  t;
update  fleet_staging
set maintenance_cost = TRIM(REPLACE(maintenance_cost,'KES',''));


select TRIM(UPPER(t.mechanic_name  )) from fleet_staging t;
update  fleet_staging
set mechanic_name = TRIM(UPPER(mechanic_name));

select t.mechanic_name  from fleet_staging t
where  t.mechanic_name  is null;  -- mechanic_name no  null values--


select t.next_service_due     from fleet_staging t
where  t.next_service_due    is null;  --next_service_due   no  null values--

SELECT TRIM(REPLACE(t.event_date , '-', '/')) FROM fleet_staging t ;
update fleet_staging t 
set event_date = TRIM(REPLACE(event_date ,'-','/'));


UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '13/05/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '21/03/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '17/04/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '03/06/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '06/02/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '14/04/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE '22/04/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE  '28/01/23';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE  '28/04/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE  '05/03/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE  '12/05/25';

UPDATE fleet_staging t
SET event_date = to_char(to_date(event_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE event_date LIKE  '04/05/25';

UPDATE fleet_staging t
SET next_service_due = to_char(to_date(next_service_due, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE next_service_due LIKE  '10/10/25';

SELECT TRIM(REPLACE(next_service_due , '-', '/')) FROM fleet_staging ;
Update fleet_staging 
set next_service_due = TRIM(REPLACE(next_service_due  ,'-','/'));


--delete duplicates from fleet_satging--
select  COUNT(distinct(log_id)) from fleet_staging t; ---102 log_ids
select COUNT(log_id )from fleet_staging;

with duplicates as (select log_id,
row_number() over(partition by log_id ) as rownumber
from fleet_staging t)

delete log_id from duplicates
where rownumber > 1;

DELETE FROM fleet_staging
WHERE log_id NOT IN (
    SELECT MIN(id)
    FROM fleet_staging
    GROUP BY log_id
);

select * from fleet_staging t; 
select * from trips_staging ts; 

----===================================-----
---CLEANING trips_staging TABLE----
select * from trips_staging ts; 
select ts.trip_id from trips_staging ts
where trip_id is null; --trip_id has no null cell

select ts.customer_name  from trips_staging ts
where customer_name   is null;  --customer_name has no null cell

select TRIM(UPPER(ts.customer_name))  from trips_staging ts;
update trips_staging 
set customer_name = TRIM(UPPER(customer_name));

select ts.customer_phone   from trips_staging ts
where customer_phone    is null;


SELECT TRIM(REPLACE(ts.customer_phone, '+254', '0')) FROM trips_staging ts;
update trips_staging 
set customer_phone = TRIM(REPLACE(customer_phone,'+254','0'));

SELECT TRIM(REPLACE(ts.customer_phone, '-', '')) FROM trips_staging ts;
update trips_staging 
set customer_phone = TRIM(REPLACE(customer_phone,'-',''));

select TRIM(UPPER(ts.customer_area)) from trips_staging ts;
update trips_staging
set customer_area = TRIM(UPPER(customer_area));

SELECT TRIM(REPLACE(ts.customer_area,'KASARRANI', 'KASARANI')) FROM trips_staging ts;
update trips_staging
set customer_area = TRIM(REPLACE(customer_area,'KASARRANI', 'KASARANI'));

SELECT TRIM(REPLACE(ts.customer_area,'PARKLLANDS', 'PARKLANDS')) FROM trips_staging ts;
update trips_staging
set customer_area = TRIM(REPLACE(customer_area,'PARKLLANDS', 'PARKLANDS'));

SELECT TRIM(REPLACE(ts.customer_area,'BURUBBURU', 'BURUBURU')) FROM trips_staging ts;
update trips_staging
set customer_area = TRIM(REPLACE(customer_area,'BURUBBURU', 'BURUBURU'));


SELECT TRIM(REPLACE(ts.customer_area,'LANGGATA','LANGATA')) FROM trips_staging ts;
update trips_staging
set customer_area = TRIM(REPLACE(customer_area,'LANGGATA','LANGATA'));

SELECT TRIM(REPLACE(ts.customer_area,'KILIMMANI','KILIMANI')) FROM trips_staging ts;
update trips_staging
set customer_area = TRIM(REPLACE(customer_area,'KILIMMANI','KILIMANI'));

SELECT TRIM(REPLACE(ts.customer_area,'CBBD','CBD')) FROM trips_staging ts;
update trips_staging
set customer_area = TRIM(REPLACE(customer_area,'CBBD','CBD'));

SELECT TRIM(REPLACE(ts.pickup_area,'KARREN','KAREN')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'KARREN','KAREN'));

select TRIM(UPPER(ts.driver_name))  from trips_staging ts;
update trips_staging 
set driver_name = TRIM(UPPER(driver_name));

SELECT TRIM(REPLACE(ts.driver_phone, '+254', '0')) FROM trips_staging ts;
update trips_staging 
set driver_phone = TRIM(REPLACE(driver_phone,'+254','0'));

SELECT TRIM(REPLACE(ts.driver_phone, '-', '')) FROM trips_staging ts;
update trips_staging 
set driver_phone = TRIM(REPLACE(driver_phone,'-',''));

select TRIM(UPPER(ts.vehicle_plate))  from trips_staging ts;
update  trips_staging
set vehicle_plate = TRIM(UPPER(vehicle_plate));

select TRIM(UPPER(ts.vehicle_make))  from trips_staging ts;
update  trips_staging
set vehicle_make = TRIM(UPPER(vehicle_make));

select TRIM(UPPER(ts.vehicle_model))  from trips_staging ts;
update trips_staging
set vehicle_model = TRIM(UPPER(vehicle_model)); 

select TRIM(UPPER(ts.pickup_area)) from trips_staging ts;
update  trips_staging
set pickup_area = TRIM(UPPER(pickup_area));

SELECT TRIM(REPLACE(ts.pickup_area,'RUNNDA', 'RUNDA')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'RUNNDA', 'RUNDA'));

SELECT TRIM(REPLACE(ts.pickup_area,'KASARRANI', 'KASARANI')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'KASARRANI', 'KASARANI'));

SELECT TRIM(REPLACE(ts.pickup_area,'LANGGATA','LANGATA')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'LANGGATA','LANGATA'));

SELECT TRIM(REPLACE(ts.pickup_area,'KILIMMANI','KILIMANI')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'KILIMMANI','KILIMANI'));

SELECT TRIM(REPLACE(ts.pickup_area,'CBBD','CBD')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'CBBD','CBD'));

SELECT TRIM(REPLACE(ts.pickup_area,'KARREN','KAREN')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'KARREN','KAREN'));

SELECT TRIM(REPLACE(ts.pickup_area ,'PARKLLANDS', 'PARKLANDS')) FROM trips_staging ts;
update trips_staging
set pickup_area = TRIM(REPLACE(pickup_area,'PARKLLANDS', 'PARKLANDS'));

select TRIM(UPPER(ts.payment_method))  from trips_staging ts;
update  trips_staging
set payment_method = TRIM(UPPER(payment_method ));

SELECT TRIM(REPLACE(ts.payment_method  ,'MPESA', 'M-PESA')) FROM trips_staging ts;
update trips_staging
set payment_method = TRIM(REPLACE(payment_method ,'MPESA', 'M-PESA'));

select TRIM(UPPER(ts.status ))  from trips_staging ts;
update  trips_staging
set status = TRIM(UPPER(status));

select TRIM(REPLACE(ts.fare_amount,'KES','' )) from trips_staging  ts;
update  trips_staging
set fare_amount = TRIM(REPLACE(fare_amount,'KES',''));

select TRIM(UPPER(ts.dropoff_area)) from trips_staging ts;
update  trips_staging
set dropoff_area = TRIM(UPPER(dropoff_area));

SELECT TRIM(REPLACE(ts.dropoff_area,'RUNNDA', 'RUNDA')) FROM trips_staging ts;
update trips_staging
set  dropoff_area = TRIM(REPLACE( dropoff_area,'RUNNDA', 'RUNDA'));

SELECT TRIM(REPLACE(ts. dropoff_area,'KASARRANI', 'KASARANI')) FROM trips_staging ts;
update trips_staging
set  dropoff_area = TRIM(REPLACE( dropoff_area,'KASARRANI', 'KASARANI'));

SELECT TRIM(REPLACE(ts.dropoff_area,'LANGGATA','LANGATA')) FROM trips_staging ts;
update trips_staging
set  dropoff_area = TRIM(REPLACE( dropoff_area,'LANGGATA','LANGATA'));

SELECT TRIM(REPLACE(ts. dropoff_area,'KILIMMANI','KILIMANI')) FROM trips_staging ts;
update trips_staging
set  dropoff_area = TRIM(REPLACE( dropoff_area,'KILIMMANI','KILIMANI'));

SELECT TRIM(REPLACE(ts.dropoff_area,'CBBD','CBD')) FROM trips_staging ts;
update trips_staging
set  dropoff_area = TRIM(REPLACE(dropoff_area,'CBBD','CBD'));

SELECT TRIM(REPLACE(dropoff_area,'KARREN','KAREN')) FROM trips_staging ts;
update trips_staging
set  dropoff_area = TRIM(REPLACE(dropoff_area,'KARREN','KAREN'));

SELECT TRIM(REPLACE(ts.dropoff_area ,'PARKLLANDS', 'PARKLANDS')) FROM trips_staging ts;
update trips_staging
set dropoff_area = TRIM(REPLACE(dropoff_area,'PARKLLANDS', 'PARKLANDS'));

SELECT TRIM(REPLACE(ts.trip_date , '-', '/')) FROM trips_staging ts;
Update trips_staging 
set trip_date = TRIM(REPLACE(trip_date ,'-','/'));


UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE  '08/01/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE  '04/05/25'; 
UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE  '02/02/25';

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '09/03/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '02/02/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '02/01/25'; 

UPDATE trips_staging
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '19/01/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '17/05/25'; 

UPDATE trips_staging
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '26/05/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '01/02/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '15/03/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '15/03/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '10/03/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '19/06/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '06/04/25'; 

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '11/02/25';

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '18/05/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '02/03/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '20/04/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '28/05/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '13/06/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '13/06/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '02/02/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '11/02/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '22/06/25'  ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '24/04/25' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '01/03/25' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '01/03/25' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '28/04/25' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '09/05/25' ;


UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '07/01/2025' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '01/04/2025' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '26/05/2025' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '24/01/2025' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '12/04/25' ;


UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '20/03/25' ;

UPDATE trips_staging 
SET trip_date = to_char(to_date(trip_date, 'DD/MM/YY'), 'YYYY-MM-DD')
WHERE trip_date LIKE '16/02/25' ;

SELECT TRIM(REPLACE(ts.distance_km  , '-', '')) FROM trips_staging ts;
Update trips_staging 
set distance_km = TRIM(REPLACE(distance_km  ,'-',''));
select * from trips_staging ts;

SELECT TRIM(REPLACE(ts.customer_rating , '6', '5')) FROM trips_staging ts;
Update trips_staging 
set customer_rating = TRIM(REPLACE(customer_rating ,'6','5'));


SELECT TRIM(REPLACE(ts.status , 'COMPLETE', 'COMPLETED')) FROM trips_staging ts;
Update trips_staging 
set status = TRIM(REPLACE(status ,'COMPLETE','COMPLETED'));

SELECT TRIM(REPLACE(ts.status , 'COMPLETEDD', 'COMPLETED')) FROM trips_staging ts;
Update trips_staging 
set status = TRIM(REPLACE(status ,'COMPLETEDD','COMPLETED'));

select * from fleet_staging t; 
select * from trips_staging ts;

select trip_id,driver_name,driver_phone,ts.vehicle_plate   from trips_staging ts
where ts.driver_name = 'HASSAN WAFULA';







