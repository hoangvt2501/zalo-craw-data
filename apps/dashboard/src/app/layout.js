import "./globals.css";

export const metadata = {
  title: "Hotel Intel Dashboard",
  description: "Operational dashboard for hotel deal intake and review.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
