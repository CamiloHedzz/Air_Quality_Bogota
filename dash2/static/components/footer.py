from dash import html

footer_content = html.Footer(
    className="footer-content",
    children=[
        html.Div(
            className="contact-info",
            children=[
                html.Div(
                    className="container_img",
                    children=[
                        html.ObjectEl(
                            type="image/svg+xml",
                            data="../../public/airQuality.svg",
                            id="footer_img"
                        ),
                        html.P(
                            "Si tienes dudas o quedaste con ganas de mas, "
                            "no dudes revisar nuestras redes sociales y "
                            "recuerda que te puedes poner en contacto con nostros, "
                            "además revisa los recursos que te hemos dejado para mayor información!"
                        ),
                        html.Div(
                            className="social-icons",
                            children=[
                                html.A(
                                    href="https://github.com/CamiloHedzz/Air_Quality_Bogota",
                                    target="_blank",
                                 
                                ),
                                html.A(
                                    href="https://www.instagram.com/cher_zi/",
                                    target="_blank",
                                  
                                ),
                                html.A(
                                    href="mailto:camilohedzz@gmail.com",
                                   
                                ),
                            ]
                        ),
                        html.Div(
                            className="resources",
                            children=[
                                html.H2("Resources"),
                                html.A(
                                    "Dash",
                                    href="https://dash.plotly.com/",
                                    target="_blank"
                                ),
                                html.A(
                                    "Bogota Catastral",
                                    href="https://bogota-laburbano.opendatasoft.com/pages/home/",
                                    target="_blank"
                                ),
                                html.A(
                                    "Datos Abiertos Bogota",
                                    href="https://datosabiertos.bogota.gov.co/",
                                    target="_blank"
                                ),
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)
