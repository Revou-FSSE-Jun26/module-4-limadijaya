// Placeholder page (T1.05) so the scaffold can be built and run. It carries no
// application behavior. The dashboard route is created later under (app)/page.tsx
// (T11.01), and this file must be removed then, because both would serve "/".
export default function PlaceholderPage() {
  return (
    <main className="mx-auto max-w-3xl p-4">
      <h1 className="text-2xl font-semibold">RevoTask</h1>
      <p className="mt-2 text-gray-600">Under construction.</p>
    </main>
  );
}
