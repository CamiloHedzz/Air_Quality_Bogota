import React, { useState } from 'react';

function ContactForm() {
    return(
    <form action="https://formsubmit.co/camilohedzz@gmail.com" method="POST">
    <div class="form-group">
        <label for="name">Nombre:</label>
        <input type="text" id="name" name="name" required></input>
    </div>
    <div class="form-group">
        <label for="email">Correo electrónico:</label>
        <input type="email" id="email" name="email" required></input>
    </div>
    <div class="form-group">
        <label for="subject">Asunto:</label>
        <input type="text" id="subject" name="subject" required></input>
    </div>
    <div class="form-group">
        <label for="comments">Comentarios:</label>
        <textarea id="comments" name="comments" required></textarea>
    </div>
    <button type="submit">Enviar</button>
    <input type="hidden" name="_next" value="http://localhost:5173/About"></input>
    </form>
  );
}

export default ContactForm;