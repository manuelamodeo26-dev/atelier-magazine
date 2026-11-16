DROP POLICY IF EXISTS "Admins can moderate comments" ON public.community_comments;
CREATE POLICY "Admins can moderate comments" ON public.community_comments
FOR UPDATE TO authenticated
USING (((SELECT auth.jwt())->'app_metadata'->>'role') = 'admin')
WITH CHECK (((SELECT auth.jwt())->'app_metadata'->>'role') = 'admin');
