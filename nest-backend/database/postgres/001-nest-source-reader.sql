-- Run as the PostgreSQL database owner after Django migrations are applied.
-- Replace rmc with the actual database name before execution.
-- This is deliberately an allow-list: new Django tables are not exposed by default.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nest_source_reader') THEN
    CREATE ROLE nest_source_reader LOGIN PASSWORD 'REPLACE_WITH_A_SECRET';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE rmc TO nest_source_reader;
GRANT USAGE ON SCHEMA public TO nest_source_reader;

GRANT SELECT ON TABLE
  public.brands,
  public.addresses_country,
  public.addresses_federal_district,
  public.addresses_type_region,
  public.addresses_timezone,
  public.addresses_region,
  public.addresses_locality_type,
  public.addresses_city,
  public.addresses_administrative_territory,
  public.addresses_administrative_territorial_unit,
  public.addresses_street_type,
  public.addresses_street,
  public.addresses_house,
  public.addresses_building,
  public.addresses_coordinates,
  public.addresses_address,
  public.contact_info,
  public.counterparty_categories,
  public.counterparty_contact_info,
  public.counterparties,
  public.counterparty_category_assignments,
  public.counterparties_contact_persons,
  public.counterparties_brands,
  public.type_of_place,
  public.nomenclature,
  public.nomenclature_tenant,
  public.discount_rule,
  public.statistic_receipt,
  public.nomenclatures_stationcredential,
  public.nomenclatures_stationinstallation,
  public.nomenclatures_stationcommandv2,
  public.availability,
  public.nomenclature_addresses,
  public.status_history,
  public.nomenclature_images,
  public.nomenclature_videos
TO nest_source_reader;

-- The site API does not need authentication secrets. Column grants supersede
-- a table-wide custom_user grant and prevent raw SQL from accessing them.
GRANT SELECT (
  id, avatar, last_name, first_name, middle_name, role, phone_number, email,
  is_active, is_staff, created, code1c
) ON public.custom_user TO nest_source_reader;
