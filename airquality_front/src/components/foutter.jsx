import square from "../assets/figures/square.jpg"

export function Footer() {    
    return(
<footer>
  <div class="footer-content">
    <div class="contact-info">
      <div class="container_img">
        <object type="image/svg+xml" data="../../public/airQuality.svg" id="footer_img"></object>
        <p>
           Si tienes dudas o quedaste con ganas de mas, 
           ponte en contacto con nostros y
           revisa los recursos que te hemos dejado
        </p>
      </div>
      <div class="social-icons">
        <a href="enlace-a-github"><i class="fab fa-github"></i></a>
        <a href="enlace-a-gmail"><i class="fas fa-envelope"></i></a>
        <a href="enlace-a-instagram"><i class="fab fa-instagram"></i></a>
      </div>
    </div>
    <div class="resources">
      <h3>Resources</h3>
      <ul>
        <li><a href="enlace-a-recurso-1">Recurso 1</a></li>
        <li><a href="enlace-a-recurso-2">Recurso 2</a></li>
        <li><a href="enlace-a-recurso-3">Recurso 3</a></li>

      </ul>
    </div>
  </div>
</footer>
    );
}
