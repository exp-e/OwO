begin;

create schema if not exists site_private;
revoke all on schema site_private from public, anon, authenticated;
create table if not exists site_private.owners (
  user_id uuid primary key references auth.users(id) on delete cascade
);
alter table site_private.owners enable row level security;
revoke all on site_private.owners from public, anon, authenticated;

create or replace function public.is_site_owner()
returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from site_private.owners where user_id = auth.uid())
$$;
revoke all on function public.is_site_owner() from public, anon;
grant execute on function public.is_site_owner() to authenticated;

create table if not exists public.locked_note_keys (
  slug text primary key,
  key_b64 text not null
);
alter table public.locked_note_keys enable row level security;
revoke all on public.locked_note_keys from public, anon, authenticated;
grant select on public.locked_note_keys to authenticated;
drop policy if exists owner_reads_note_keys on public.locked_note_keys;
create policy owner_reads_note_keys on public.locked_note_keys
  for select to authenticated using ((select public.is_site_owner()));

-- Keep existing visitor reads, posts and likes, but never accept a visitor's
-- claimed owner badge or allow a visitor to remove someone else's post.
create or replace function site_private.guard_guestbook_owner()
returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  if current_setting('role', true) not in ('anon', 'authenticated') or public.is_site_owner() then
    return new;
  end if;
  if tg_op = 'INSERT' then
    if coalesce(new.is_admin, false) then
      raise exception 'Only the site owner can publish as owner' using errcode = '42501';
    end if;
  elsif (to_jsonb(new) - 'likes') is distinct from (to_jsonb(old) - 'likes') then
    raise exception 'Visitors can only update likes' using errcode = '42501';
  end if;
  return new;
end;
$$;
revoke all on function site_private.guard_guestbook_owner() from public, anon, authenticated;
drop trigger if exists guard_guestbook_owner on public.guestbook;
create trigger guard_guestbook_owner before insert or update on public.guestbook
  for each row execute function site_private.guard_guestbook_owner();

alter table public.guestbook enable row level security;
drop policy if exists owner_only_guestbook_delete on public.guestbook;
create policy owner_only_guestbook_delete on public.guestbook as restrictive
  for delete to authenticated using ((select public.is_site_owner()));
drop policy if exists visitor_cannot_delete_guestbook on public.guestbook;
create policy visitor_cannot_delete_guestbook on public.guestbook as restrictive
  for delete to anon using (false);
drop policy if exists owner_can_delete_guestbook on public.guestbook;
create policy owner_can_delete_guestbook on public.guestbook
  for delete to authenticated using ((select public.is_site_owner()));
drop policy if exists owner_can_insert_guestbook on public.guestbook;
create policy owner_can_insert_guestbook on public.guestbook
  for insert to authenticated with check ((select public.is_site_owner()));

commit;
