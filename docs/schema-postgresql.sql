-- Le Réflexe Dos — schéma PostgreSQL de départ
-- PostgreSQL 15+ / compatible Supabase.
-- À adapter par migrations versionnées. Ne stocker aucune donnée de santé au MVP.

create extension if not exists pgcrypto;

create type content_kind as enum ('page','article','email','guide','video_script','social_post');
create type workflow_status as enum ('idea','brief','draft','source_check','medical_review','ready','published','rejected','archived');
create type review_decision as enum ('approved','changes_requested','rejected');
create type order_status as enum ('pending','paid','refunded','partially_refunded','failed','cancelled');
create type consent_action as enum ('granted','withdrawn');

create table profiles (
  id uuid primary key,
  email text not null unique,
  display_name text,
  role text not null default 'customer' check (role in ('customer','editor','reviewer','publisher','admin')),
  locale text not null default 'fr-FR',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table consent_events (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references profiles(id) on delete set null,
  email text,
  purpose text not null,
  action consent_action not null,
  policy_version text not null,
  source text not null,
  evidence jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  check (profile_id is not null or email is not null)
);
create index consent_events_lookup_idx on consent_events (coalesce(profile_id::text, email), purpose, occurred_at desc);

create table lead_subscriptions (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  status text not null default 'pending' check (status in ('pending','active','unsubscribed','bounced','complained')),
  source text not null,
  confirmation_token_hash text,
  confirmed_at timestamptz,
  unsubscribed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table products (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text not null,
  status text not null default 'draft' check (status in ('draft','active','retired')),
  access_duration_days integer,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table product_prices (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references products(id) on delete cascade,
  stripe_price_id text unique,
  currency char(3) not null default 'EUR',
  amount_cents integer not null check (amount_cents >= 0),
  starts_at timestamptz not null default now(),
  ends_at timestamptz,
  label text,
  created_at timestamptz not null default now(),
  check (ends_at is null or ends_at > starts_at)
);
create index product_prices_active_idx on product_prices (product_id, starts_at desc, ends_at);

create table orders (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references profiles(id) on delete set null,
  customer_email text not null,
  stripe_checkout_session_id text unique,
  stripe_payment_intent_id text unique,
  status order_status not null default 'pending',
  currency char(3) not null default 'EUR',
  subtotal_cents integer not null default 0,
  tax_cents integer not null default 0,
  total_cents integer not null default 0,
  accepted_immediate_delivery_at timestamptz,
  acknowledged_withdrawal_loss_at timestamptz,
  created_at timestamptz not null default now(),
  paid_at timestamptz,
  updated_at timestamptz not null default now()
);
create index orders_customer_idx on orders (customer_email, created_at desc);

create table order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders(id) on delete cascade,
  product_id uuid not null references products(id),
  product_price_id uuid references product_prices(id),
  product_name_snapshot text not null,
  unit_amount_cents integer not null check (unit_amount_cents >= 0),
  quantity integer not null default 1 check (quantity > 0),
  created_at timestamptz not null default now()
);

create table entitlements (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references profiles(id) on delete cascade,
  customer_email text not null,
  product_id uuid not null references products(id),
  order_item_id uuid references order_items(id),
  starts_at timestamptz not null default now(),
  expires_at timestamptz,
  revoked_at timestamptz,
  revoke_reason text,
  created_at timestamptz not null default now()
);
create unique index entitlements_active_unique on entitlements (customer_email, product_id) where revoked_at is null;

create table digital_assets (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references products(id) on delete cascade,
  storage_key text not null unique,
  filename text not null,
  mime_type text not null,
  version text not null,
  sha256 text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table download_events (
  id uuid primary key default gen_random_uuid(),
  entitlement_id uuid not null references entitlements(id) on delete cascade,
  digital_asset_id uuid not null references digital_assets(id),
  ip_hash text,
  user_agent_hash text,
  downloaded_at timestamptz not null default now()
);
create index download_events_entitlement_idx on download_events (entitlement_id, downloaded_at desc);

create table content_items (
  id uuid primary key default gen_random_uuid(),
  kind content_kind not null,
  slug text not null unique,
  title text not null,
  owner_id uuid references profiles(id) on delete set null,
  health_content boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table content_versions (
  id uuid primary key default gen_random_uuid(),
  content_item_id uuid not null references content_items(id) on delete cascade,
  version_number integer not null check (version_number > 0),
  status workflow_status not null default 'draft',
  body_markdown text not null,
  summary text,
  seo_title text,
  seo_description text,
  prompt_version text,
  generated_by_model text,
  content_hash text not null,
  created_by uuid references profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  published_at timestamptz,
  unique (content_item_id, version_number)
);
create index content_versions_workflow_idx on content_versions (status, created_at);

create table sources (
  id uuid primary key default gen_random_uuid(),
  canonical_url text not null unique,
  publisher text not null,
  title text not null,
  source_type text not null check (source_type in ('official_guideline','official_page','research','legal','commercial_benchmark','other')),
  published_on date,
  accessed_at timestamptz not null default now(),
  content_hash text,
  archived_url text,
  notes text
);

create table content_sources (
  content_version_id uuid not null references content_versions(id) on delete cascade,
  source_id uuid not null references sources(id) on delete restrict,
  citation_label text,
  supports_claim text,
  primary key (content_version_id, source_id)
);

create table claims (
  id uuid primary key default gen_random_uuid(),
  content_version_id uuid not null references content_versions(id) on delete cascade,
  claim_text text not null,
  risk_level text not null check (risk_level in ('low','medium','high')),
  verification_status text not null default 'pending' check (verification_status in ('pending','supported','rewritten','removed')),
  reviewer_note text,
  verified_at timestamptz
);
create index claims_pending_idx on claims (content_version_id, verification_status);

create table medical_reviews (
  id uuid primary key default gen_random_uuid(),
  content_version_id uuid not null references content_versions(id) on delete cascade,
  reviewer_id uuid not null references profiles(id),
  reviewer_qualification text not null,
  decision review_decision not null,
  scope text not null,
  notes text,
  reviewed_at timestamptz not null default now(),
  valid_until timestamptz,
  unique (content_version_id, reviewer_id, reviewed_at)
);
create index medical_reviews_valid_idx on medical_reviews (content_version_id, decision, valid_until);

create table correction_reports (
  id uuid primary key default gen_random_uuid(),
  content_item_id uuid not null references content_items(id),
  reporter_email text,
  category text not null check (category in ('medical','source','clarity','accessibility','legal','other')),
  message text not null,
  status text not null default 'open' check (status in ('open','triaged','resolved','dismissed')),
  resolution_note text,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  channel text not null,
  objective text not null,
  status text not null default 'draft' check (status in ('draft','scheduled','active','paused','completed')),
  starts_at timestamptz,
  ends_at timestamptz,
  budget_cents integer check (budget_cents >= 0),
  created_at timestamptz not null default now()
);

create table campaign_assets (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  content_version_id uuid references content_versions(id) on delete set null,
  format text not null,
  destination_url text,
  utm jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table affiliate_links (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  merchant text not null,
  destination_url text not null,
  disclosure_text text not null,
  commission_model text,
  active boolean not null default true,
  last_verified_at timestamptz,
  created_at timestamptz not null default now()
);

create table affiliate_clicks (
  id uuid primary key default gen_random_uuid(),
  affiliate_link_id uuid not null references affiliate_links(id),
  content_item_id uuid references content_items(id) on delete set null,
  campaign_id uuid references campaigns(id) on delete set null,
  anonymous_session_id uuid,
  clicked_at timestamptz not null default now()
);
create index affiliate_clicks_reporting_idx on affiliate_clicks (affiliate_link_id, clicked_at);

create table seo_keywords (
  id uuid primary key default gen_random_uuid(),
  keyword text not null,
  locale text not null default 'fr-FR',
  cluster text not null,
  intent text not null check (intent in ('informational','commercial','transactional','navigational')),
  monthly_volume integer,
  difficulty numeric(5,2),
  target_content_item_id uuid references content_items(id) on delete set null,
  source text,
  measured_at date,
  unique (keyword, locale)
);

create table source_candidates (
  id uuid primary key default gen_random_uuid(),
  url text not null,
  title text,
  publisher text,
  observed_at timestamptz not null default now(),
  content_hash text,
  apify_dataset_id text,
  status text not null default 'new' check (status in ('new','accepted','rejected','duplicate')),
  payload jsonb not null default '{}'::jsonb,
  unique (url, content_hash)
);

create table automation_runs (
  id uuid primary key default gen_random_uuid(),
  provider text not null check (provider in ('openrouter','apify','brevo','stripe','internal')),
  job_type text not null,
  external_run_id text,
  status text not null check (status in ('queued','running','succeeded','failed','cancelled')),
  input_hash text,
  model_or_actor text,
  prompt_version text,
  input_tokens integer,
  output_tokens integer,
  cost_microusd bigint,
  duration_ms integer,
  error_code text,
  metadata jsonb not null default '{}'::jsonb,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);
create index automation_runs_ops_idx on automation_runs (provider, job_type, created_at desc);

create table admin_audit_log (
  id bigint generated always as identity primary key,
  actor_id uuid references profiles(id) on delete set null,
  action text not null,
  entity_type text not null,
  entity_id uuid,
  before_state jsonb,
  after_state jsonb,
  occurred_at timestamptz not null default now()
);

-- Une vue de publication ne retourne qu'une version explicitement publiée.
create view published_content as
select distinct on (ci.id)
  ci.id,
  ci.kind,
  ci.slug,
  ci.title,
  cv.id as version_id,
  cv.version_number,
  cv.body_markdown,
  cv.summary,
  cv.seo_title,
  cv.seo_description,
  cv.published_at
from content_items ci
join content_versions cv on cv.content_item_id = ci.id
where cv.status = 'published'
order by ci.id, cv.version_number desc;

-- Contrôle applicatif à appeler avant publication d'un contenu santé.
create or replace function content_version_can_publish(target_version uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from content_versions cv
    join content_items ci on ci.id = cv.content_item_id
    where cv.id = target_version
      and cv.status in ('ready','published')
      and not exists (
        select 1 from claims c
        where c.content_version_id = cv.id
          and c.verification_status = 'pending'
      )
      and (
        ci.health_content = false
        or exists (
          select 1 from medical_reviews mr
          where mr.content_version_id = cv.id
            and mr.decision = 'approved'
            and (mr.valid_until is null or mr.valid_until > now())
        )
      )
  );
$$;

-- RLS : exemples minimaux. Affiner selon le fournisseur d'authentification.
alter table profiles enable row level security;
alter table orders enable row level security;
alter table entitlements enable row level security;
alter table download_events enable row level security;

-- Supabase : auth.uid() est disponible lorsque l'utilisateur est authentifié.
-- create policy "profile reads self" on profiles for select using (id = auth.uid());
-- create policy "orders read self" on orders for select using (profile_id = auth.uid());
-- create policy "entitlements read self" on entitlements for select using (profile_id = auth.uid());

-- Les opérations d'écriture commerciales et éditoriales doivent passer par le serveur.
-- Ne jamais exposer la service-role key dans le navigateur.
