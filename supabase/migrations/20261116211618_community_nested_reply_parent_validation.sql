-- Keep threaded replies available while validating the real parent row.
-- A reply must target a published comment in the same discussion.
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
    )
  )
);
