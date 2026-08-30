import { type FormEvent, useState } from "react";
import { assetUrl } from "../lib/assets";

const CONTACT_EMAIL = "tl4732@nyu.edu";

export function ContactPage() {
  const [sent, setSent] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const name = String(data.get("name") ?? "").trim();
    const email = String(data.get("email") ?? "").trim();
    const message = String(data.get("message") ?? "").trim();
    const subject = encodeURIComponent(`Bagzine note from ${name || "a reader"}`);
    const body = encodeURIComponent(`${message}\n\n— ${name}${email ? ` (${email})` : ""}`);
    window.location.href = `mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`;
    setSent(true);
  }

  return (
    <section className="contact-page" aria-label="Contact">
      <div className="contact-page-left">
        <h1>Contact</h1>
        <p className="contact-page-lede">Reach out to the creator.</p>

        <ul className="contact-details">
          <li>
            <span>Email:</span>{" "}
            <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
          </li>
          <li>
            <span>LinkedIn:</span>{" "}
            <a
              href="https://www.linkedin.com/in/tsaitung/"
              target="_blank"
              rel="noreferrer"
            >
              Lucy Lu
            </a>
          </li>
          <li>
            <span>GitHub:</span>{" "}
            <a href="https://github.com/tl4732-cyber" target="_blank" rel="noreferrer">
              tl4732-cyber
            </a>
          </li>
        </ul>

        <form className="contact-form" onSubmit={handleSubmit}>
          <label>
            Name
            <input name="name" type="text" autoComplete="name" required />
          </label>
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Message
            <textarea name="message" rows={2} required />
          </label>
          <button type="submit">Send message</button>
          {sent && <p className="muted">Your mail app should open with the note attached.</p>}
        </form>
      </div>

      <aside className="contact-page-right">
        <div className="contact-page-visual">
          <img
            src={assetUrl("images/IMG_088B311DF51F-1-modified.png")}
            alt="Portrait illustration of Lucy"
            className="contact-page-portrait"
          />
          <p className="contact-speech-bubble" role="status">
            Thanks for visiting my site!
          </p>
        </div>
      </aside>
    </section>
  );
}
