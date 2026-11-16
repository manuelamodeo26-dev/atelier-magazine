-- Restrict direct RPC execution of the trigger-only SECURITY DEFINER function.
-- The trigger can still invoke this function without granting EXECUTE to API roles.
REVOKE EXECUTE ON FUNCTION public.protect_profile_admin_fields() FROM PUBLIC, anon, authenticated;

-- Validate replies against the actual parent comment and its discussion.
-- Replies are limited to top-level published comments to avoid unbounded nesting.
DROP POLICY IF EXISTS "Signed in users can comment on visible discussions" ON public.community_comments;
CREATE POLICY "Signed in users can comment on visible discussions"
ON public.community_comments
FOR INSERT
TO authenticated
WITH CHECK (
  author_id = (SELECT auth.uid())
  AND status = 'published'
  AND EXISTS (
    SELECT 1
    FROM public.community_discussions d
    WHERE d.id = community_comments.discussion_id
      AND d.status = 'published'
  )
  AND (
    parent_comment_id IS NULL
    OR EXISTS (
      SELECT 1
      FROM public.community_comments parent
      WHERE parent.id = community_comments.parent_comment_id
        AND parent.discussion_id = community_comments.discussion_id
        AND parent.status = 'published'
        AND parent.parent_comment_id IS NULL
    )
  )
);
