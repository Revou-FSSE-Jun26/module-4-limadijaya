import ErrorState from "@/components/boards/ErrorState";
import ProfileForm from "@/components/profile/ProfileForm";
import { serverGetResult } from "@/lib/serverApi.server";
import type { UserPublic } from "@/types/api";

/** Profile: Server Component that loads the current user, then renders the update form (FRONT-010). */
export default async function ProfilePage() {
  const result = await serverGetResult<UserPublic>("/api/users/me");
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Your profile</h1>
      {result.error !== null ? <ErrorState message={result.error} /> : <ProfileForm key={result.data.id} />}
    </div>
  );
}