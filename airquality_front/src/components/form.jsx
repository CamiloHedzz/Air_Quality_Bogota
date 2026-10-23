function ContactForm() {
  return (
    <form className="contact-form" action="https://formsubmit.co/camilohedzz@gmail.com" method="POST">
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
        <input type="text" id="subject" name="subject" required />
      </div>
      <div className="form-group">
        <label htmlFor="comments">Comentarios:</label>
        <textarea id="comments" name="comments" required />
      </div>
      <button type="submit">Enviar</button>
      <input type="hidden" name="_next" value="http://localhost:5173/About" />
    </form>
  );
}

export default ContactForm;
