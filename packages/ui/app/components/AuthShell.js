import Icon from "./Icon";
import Spot from "./Spot";

// Two-column layout for log in and sign up: the form, and a short panel about the product.
export default function AuthShell({ children }) {
  return (
    <div className="auth">
      <div className="auth-form">{children}</div>
      <aside className="auth-side">
        <Spot kind="board" />
        <h2>Your week, on one board</h2>
        <ul>
          <li><Icon name="alert" /> Clash warnings before you double-book anyone</li>
          <li><Icon name="mail" /> Technicians get an email when a job is assigned</li>
          <li><Icon name="phone" /> A phone view for the person on site</li>
        </ul>
      </aside>
    </div>
  );
}
