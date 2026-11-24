import BaseButton from "@/components/shared/BaseButton";

export default function BoardNotFound() {
  return (
    <div className="mx-auto max-w-md space-y-3 py-10 text-center">
      <h1 className="text-xl font-semibold">Board not found</h1>
      <p className="text-slate-600">This board does not exist, or you are not a member of it.</p>
      <BaseButton href="/">Back to your boards</BaseButton>
    </div>
  );
}