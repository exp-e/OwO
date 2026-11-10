begin;

alter table public.memo_comments enable row level security;
grant select, insert on public.memo_comments to anon, authenticated;
grant delete on public.memo_comments to authenticated;
revoke update, delete on public.memo_comments from public, anon;
revoke update on public.memo_comments from authenticated;

drop policy if exists site_comments_read on public.memo_comments;
create policy site_comments_read on public.memo_comments
  for select to anon, authenticated using (true);
drop policy if exists site_comments_insert on public.memo_comments;
create policy site_comments_insert on public.memo_comments
  for insert to anon, authenticated with check (true);

-- Restrictive policies still apply if an older permissive policy exists.
drop policy if exists site_comments_anon_no_badge on public.memo_comments;
create policy site_comments_anon_no_badge on public.memo_comments as restrictive
  for insert to anon with check (not coalesce(is_admin, false));
drop policy if exists site_comments_owner_badge on public.memo_comments;
create policy site_comments_owner_badge on public.memo_comments as restrictive
  for insert to authenticated
  with check (not coalesce(is_admin, false) or (select public.is_site_owner()));
drop policy if exists site_comments_no_update on public.memo_comments;
create policy site_comments_no_update on public.memo_comments as restrictive
  for update to anon, authenticated using (false) with check (false);

drop policy if exists site_comments_anon_no_delete on public.memo_comments;
create policy site_comments_anon_no_delete on public.memo_comments as restrictive
  for delete to anon using (false);
drop policy if exists site_comments_owner_only_delete on public.memo_comments;
create policy site_comments_owner_only_delete on public.memo_comments as restrictive
  for delete to authenticated using ((select public.is_site_owner()));
drop policy if exists site_comments_owner_delete on public.memo_comments;
create policy site_comments_owner_delete on public.memo_comments
  for delete to authenticated using ((select public.is_site_owner()));

commit;
