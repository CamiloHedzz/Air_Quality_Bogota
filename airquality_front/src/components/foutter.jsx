import git from "../assets/figures/github.png"
import ins from "../assets/figures/instagram.png"
import mail from "../assets/figures/correo.png"


export function Footer() {    
    return(
        <footer>
            <div class="footer-content">
                <div class="contact-info">
                    <div class="container_img">
                        <object type="image/svg+xml" data="../../public/airQuality.svg" id="footer_img"></object>
                        <p>
                        Si tienes dudas o quedaste con ganas de mas,
                        no dudes revisar nuestras redes sociales y 
                        recuerda que te pudes poner en contacto con nostros, a demas
                        revisa los recursos que te hemos dejado para mayor informacion!
                        </p>
                        <div class="social-icons">
                            <a href="https://github.com/CamiloHedzz/Air_Quality_Bogota" target="_blank"><img src={git} alt="github"/></a>
                            <a href="https://www.instagram.com/cher_zi/" target="_blank"><img src={ins} alt="instagram"/></a>
                            <a href="mailto:camilohedzz@gmail.com"><img src={mail} alt="email"/></a>
                        </div>
                        <div class="resources">
                        <h2>Resources</h2>
                            <a href="https://dash.plotly.com/"  target="_blank">Dash</a>
                            <a href="https://bogota-laburbano.opendatasoft.com/pages/home/"  target="_blank">Bogota Catastral</a>
                            <a href="https://datosabiertos.bogota.gov.co/" target="_blank">Datos Abiertos Bogota</a> 
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
