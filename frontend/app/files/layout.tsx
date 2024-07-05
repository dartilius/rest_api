export default function BlogLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-row items-center justify-center gap-4">
      {children}
    </section>
  );
}
