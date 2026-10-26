import { useLanguage } from "../i18n/useLanguage";
function ContactForm() {
  const { localize } = useLanguage();
  const returnUrl = new URL("/About#contact", window.location.origin).href;

  return (
    localize(<form className="contact-form" action="https://formsubmit.co/camilohedzz@gmail.com" method="POST">
      <div className="form-group">
        <label htmlFor="name">Nombre:</label>
        <input type="text" id="name" name="name" autoComplete="name" required />
      </div>
      <div className="form-group">
        <label htmlFor="email">Correo electrónico:</label>
        <input type="email" id="email" name="email" autoComplete="email" required />
      </div>
      <div className="form-group">
        <label htmlFor="subject">Asunto:</label>
        <input type="text" id="subject" name="_subject" required />
      </div>
      <div className="form-group">
        <label htmlFor="comments">Comentarios:</label>
        <textarea id="comments" name="comments" required />
      </div>
      <button type="submit">Enviar</button>
      <input type="hidden" name="_template" value="table" />
      <input type="hidden" name="_next" value={returnUrl} />
    </form>)
  );
}

export default ContactForm;
