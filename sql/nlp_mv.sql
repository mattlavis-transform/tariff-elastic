-- public.goods_nomenclature_description_periods source

CREATE OR REPLACE VIEW public.goods_nomenclature_description_periods
AS SELECT goods_nomenclature_description_periods1.goods_nomenclature_description_period_sid,
    goods_nomenclature_description_periods1.goods_nomenclature_sid,
    goods_nomenclature_description_periods1.validity_start_date,
    goods_nomenclature_description_periods1.goods_nomenclature_item_id,
    goods_nomenclature_description_periods1.productline_suffix,
    goods_nomenclature_description_periods1.validity_end_date,
    goods_nomenclature_description_periods1.oid,
    goods_nomenclature_description_periods1.operation,
    goods_nomenclature_description_periods1.operation_date,
    goods_nomenclature_description_periods1.filename
   FROM goods_nomenclature_description_periods_oplog goods_nomenclature_description_periods1
  WHERE (goods_nomenclature_description_periods1.oid IN ( SELECT max(goods_nomenclature_description_periods2.oid) AS max
           FROM goods_nomenclature_description_periods_oplog goods_nomenclature_description_periods2
          WHERE goods_nomenclature_description_periods1.goods_nomenclature_description_period_sid = goods_nomenclature_description_periods2.goods_nomenclature_description_period_sid)) AND goods_nomenclature_description_periods1.operation::text <> 'D'::text;


-- public.goods_nomenclature_descriptions source

CREATE OR REPLACE VIEW public.goods_nomenclature_descriptions
AS SELECT goods_nomenclature_descriptions1.goods_nomenclature_description_period_sid,
    goods_nomenclature_descriptions1.language_id,
    goods_nomenclature_descriptions1.goods_nomenclature_sid,
    goods_nomenclature_descriptions1.goods_nomenclature_item_id,
    goods_nomenclature_descriptions1.productline_suffix,
    goods_nomenclature_descriptions1.description,
    goods_nomenclature_descriptions1.oid,
    goods_nomenclature_descriptions1.operation,
    goods_nomenclature_descriptions1.operation_date,
    goods_nomenclature_descriptions1.filename
   FROM goods_nomenclature_descriptions_oplog goods_nomenclature_descriptions1
  WHERE (goods_nomenclature_descriptions1.oid IN ( SELECT max(goods_nomenclature_descriptions2.oid) AS max
           FROM goods_nomenclature_descriptions_oplog goods_nomenclature_descriptions2
          WHERE goods_nomenclature_descriptions1.goods_nomenclature_sid = goods_nomenclature_descriptions2.goods_nomenclature_sid AND goods_nomenclature_descriptions1.goods_nomenclature_description_period_sid = goods_nomenclature_descriptions2.goods_nomenclature_description_period_sid)) AND goods_nomenclature_descriptions1.operation::text <> 'D'::text;


-- public.goods_nomenclature_indents source

CREATE OR REPLACE VIEW public.goods_nomenclature_indents
AS SELECT goods_nomenclature_indents1.goods_nomenclature_indent_sid,
    goods_nomenclature_indents1.goods_nomenclature_sid,
    goods_nomenclature_indents1.validity_start_date,
    goods_nomenclature_indents1.number_indents,
    goods_nomenclature_indents1.goods_nomenclature_item_id,
    goods_nomenclature_indents1.productline_suffix,
    goods_nomenclature_indents1.validity_end_date,
    goods_nomenclature_indents1.oid,
    goods_nomenclature_indents1.operation,
    goods_nomenclature_indents1.operation_date,
    goods_nomenclature_indents1.filename
   FROM goods_nomenclature_indents_oplog goods_nomenclature_indents1
  WHERE (goods_nomenclature_indents1.oid IN ( SELECT max(goods_nomenclature_indents2.oid) AS max
           FROM goods_nomenclature_indents_oplog goods_nomenclature_indents2
          WHERE goods_nomenclature_indents1.goods_nomenclature_indent_sid = goods_nomenclature_indents2.goods_nomenclature_indent_sid)) AND goods_nomenclature_indents1.operation::text <> 'D'::text;


-- public.goods_nomenclatures source

CREATE OR REPLACE VIEW public.goods_nomenclatures
AS SELECT goods_nomenclatures1.goods_nomenclature_sid,
    goods_nomenclatures1.goods_nomenclature_item_id,
    goods_nomenclatures1.producline_suffix,
    goods_nomenclatures1.validity_start_date,
    goods_nomenclatures1.validity_end_date,
    goods_nomenclatures1.statistical_indicator,
    goods_nomenclatures1.oid,
    goods_nomenclatures1.operation,
    goods_nomenclatures1.operation_date,
    goods_nomenclatures1.filename
   FROM goods_nomenclatures_oplog goods_nomenclatures1
  WHERE (goods_nomenclatures1.oid IN ( SELECT max(goods_nomenclatures2.oid) AS max
           FROM goods_nomenclatures_oplog goods_nomenclatures2
          WHERE goods_nomenclatures1.goods_nomenclature_sid = goods_nomenclatures2.goods_nomenclature_sid)) AND goods_nomenclatures1.operation::text <> 'D'::text;
         
         


SELECT gn.goods_nomenclature_sid,
    gn.goods_nomenclature_item_id,
    gn.producline_suffix,
    gn.validity_start_date,
    gn.validity_end_date,
    gnd.description,
    gndp.validity_start_date AS description_start_date,
    gni.number_indents,
    gni.validity_start_date AS indent_start_date
   FROM goods_nomenclatures gn,
    goods_nomenclature_description_periods gndp,
    goods_nomenclature_descriptions gnd,
    goods_nomenclature_indents gni
  WHERE gn.goods_nomenclature_sid = gnd.goods_nomenclature_sid AND gn.goods_nomenclature_sid = gndp.goods_nomenclature_sid AND gn.goods_nomenclature_sid = gni.goods_nomenclature_sid
  ORDER BY gn.goods_nomenclature_item_id, gn.producline_suffix
