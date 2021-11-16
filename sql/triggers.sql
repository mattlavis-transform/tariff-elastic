CREATE TABLE emp (
    empname text,
    salary integer,
    last_date timestamp,
    last_user text
);

CREATE FUNCTION emp_stamp() RETURNS trigger AS $emp_stamp$
    BEGIN
        -- Check that empname and salary are given
        IF NEW.empname IS NULL THEN
            RAISE EXCEPTION 'empname cannot be null';
        END IF;
        IF NEW.salary IS NULL THEN
            RAISE EXCEPTION '% cannot have null salary', NEW.empname;
        END IF;

        -- Who works for us when she must pay for it?
        IF NEW.salary < 0 THEN
            RAISE EXCEPTION '% cannot have a negative salary', NEW.empname;
        END IF;

        -- Remember who changed the payroll when
        NEW.last_date := current_timestamp;
        NEW.last_user := current_user;
        RETURN NEW;
    END;
$emp_stamp$ LANGUAGE plpgsql;

CREATE FUNCTION emp_stamp2() RETURNS trigger AS $emp_stamp2$
    BEGIN
        -- Check that empname and salary are given
        IF NEW.empname IS NULL THEN
            RAISE EXCEPTION 'empname cannot be null';
        END IF;
        IF NEW.salary IS NULL THEN
            RAISE EXCEPTION '% cannot have null salary', NEW.empname;
        END IF;

        -- Who works for us when she must pay for it?
        IF NEW.salary < 0 THEN
            RAISE EXCEPTION '% cannot have a negative salary', NEW.empname;
        END IF;

        -- Remember who changed the payroll when
        NEW.last_date := current_timestamp;
        NEW.last_user := current_user;
        RETURN NEW;
    END;
$emp_stamp2$ LANGUAGE plpgsql;



CREATE TRIGGER emp_stamp2 BEFORE INSERT OR UPDATE ON emp
    FOR EACH ROW EXECUTE PROCEDURE emp_stamp2();
    
   
update goods_nomenclature_descriptions_oplog
set description = 'LIVE ANIMATION'
where oid = 152;

select description, vectors from goods_nomenclature_descriptions_oplog
where oid = 152;

SELECT goods_nomenclature_item_id, description, vectors
FROM goods_nomenclature_descriptions_oplog  
WHERE vectors @@ to_tsquery('lamb')
order by 
ts_rank( to_tsvector('cheese'), plainto_tsquery('cheese'), 1) desc;


SELECT goods_nomenclature_item_id, description, vectors
FROM goods_nomenclature_descriptions_oplog  
WHERE description like '%cheese%';



select distinct on (gn.goods_nomenclature_sid)
gn.goods_nomenclature_item_id, gn.producline_suffix, gnd.description,
ts_rank(to_tsvector('hippoglossus'), to_tsquery('hippoglossus'), 1)
from goods_nomenclatures_oplog gn, goods_nomenclature_descriptions_oplog gnd,
goods_nomenclature_description_periods_oplog gndp 
where gn.goods_nomenclature_sid = gnd.goods_nomenclature_sid 
and gn.goods_nomenclature_sid = gndp.goods_nomenclature_sid
and gnd.goods_nomenclature_sid = gndp.goods_nomenclature_sid
and gn.validity_end_date is null
and gnd.vectors @@ to_tsquery('hippoglossus')
and gn.validity_start_date <= '2021-11-12'
and (gn.validity_end_date >= '2021-11-12' or gn.validity_end_date is null) 
order by gn.goods_nomenclature_sid, gndp.validity_start_date desc,
ts_rank(to_tsvector('hippoglossus'), to_tsquery('hippoglossus'), 1) desc;

