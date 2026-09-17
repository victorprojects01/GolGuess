-- Execute no SQL Editor do projeto ucubzsvrlmlcbzrmxjda.
-- O navegador pode ler apenas a classificação do dia; somente o servidor grava.
create table if not exists public.daily_rankings (
  day date not null,
  visitor text not null,
  nickname text not null,
  country_code text not null default 'UN',
  players_score integer not null check (players_score between 0 and 100),
  teams_score integer not null check (teams_score between 0 and 100),
  top10_score integer not null check (top10_score between 0 and 100),
  total_score integer not null check (total_score = players_score + teams_score + top10_score),
  submitted_at timestamptz not null default now(),
  constraint daily_rankings_pk primary key (day, visitor),
  constraint daily_rankings_nickname_check check (char_length(nickname) between 3 and 20),
  constraint daily_rankings_country_code_check check (country_code ~ '^[A-Z]{2}$')
);

-- Migra instalações existentes sem perder a classificação atual.
alter table public.daily_rankings
  add column if not exists country_code text not null default 'UN';

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'daily_rankings_country_code_check'
      and conrelid = 'public.daily_rankings'::regclass
  ) then
    alter table public.daily_rankings
      add constraint daily_rankings_country_code_check
      check (country_code ~ '^[A-Z]{2}$');
  end if;
end $$;

create index if not exists daily_rankings_order
  on public.daily_rankings (day, total_score desc, submitted_at asc, visitor asc);

alter table public.daily_rankings enable row level security;

-- Supabase pode conceder privilégios padrão a novas tabelas de public.
-- Revogue-os explicitamente antes de abrir somente as colunas públicas.
revoke all on table public.daily_rankings from public, anon, authenticated;
grant select (day, nickname, country_code, players_score, teams_score, top10_score,
              total_score, submitted_at)
  on public.daily_rankings to anon, authenticated;
grant select, insert, update, delete on table public.daily_rankings to service_role;

drop policy if exists "Leitura do ranking de hoje" on public.daily_rankings;
create policy "Leitura do ranking de hoje"
  on public.daily_rankings for select
  to anon, authenticated
  using (day = (now() at time zone 'America/Sao_Paulo')::date);

-- Nenhuma policy de INSERT, UPDATE ou DELETE é criada para anon/authenticated.
-- service_role é exclusivo do servidor e contorna RLS; nunca o publique.
