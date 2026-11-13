import "@fontsource-variable/hanken-grotesk";
import "./globals.css";
import Nav from "./components/Nav";

export const metadata = {
  title: "WebAwesome Scheduler",
  description: "Job scheduling and dispatch",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main>{children}</main>
      </body>
    </html>
  );
}
