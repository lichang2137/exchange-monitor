interface HeaderProps {
  title?: string;
}

export function Header({ title = 'Exchange Monitor' }: HeaderProps) {
  return (
    <header className="header">
      <h1>🚀 {title}</h1>
    </header>
  );
}
